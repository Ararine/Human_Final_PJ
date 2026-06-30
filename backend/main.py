import logging
import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import payment

from core.logger import setup_logging
from routes import admin, analysis, notification, oauth, post, report, setting, subscription, uploads, worker
from services import subscription_scheduler


setup_logging()

logger = logging.getLogger(__name__)
logger.info("backend server is running...")

_LOCAL_WORKER_DIR = Path(__file__).resolve().parent / "local_worker"
if str(_LOCAL_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(_LOCAL_WORKER_DIR))


def check_and_migrate_db():
    from utils.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE plans ADD COLUMN IF NOT EXISTS yearly_price_amount integer;"))
        db.execute(text("ALTER TABLE plans ADD COLUMN IF NOT EXISTS yearly_credits integer;"))
        db.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS billing_period_days integer NOT NULL DEFAULT 30;"))
        db.commit()
        logger.info("Database migration check (yearly plan columns, subscription billing_period_days) completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error("Failed to migrate database (yearly columns check): %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 서버 기동 시 누락된 DB 컬럼 자동 복구 마이그레이션 실행
    check_and_migrate_db()

    settings = subscription_scheduler.get_scheduler_settings()
    subscription_scheduler_task = subscription_scheduler.start_subscription_scheduler(
        enabled=settings.enabled,
        interval_seconds=settings.interval_seconds,
        batch_limit=settings.batch_limit,
    )

    try:
        from core.worker_event import WORKER_EVENT
        from local_worker import start_background_worker

        start_background_worker(wake_event=WORKER_EVENT)
        logger.info("local_worker background thread started")
    except Exception as exc:
        logger.warning("local_worker start failed; server will continue: %s", exc)

    try:
        from services.file_cleanup import start_cleanup_scheduler

        start_cleanup_scheduler()
    except Exception as exc:
        logger.warning("file cleanup scheduler start failed; server will continue: %s", exc)

    try:
        yield
    finally:
        await subscription_scheduler.stop_subscription_scheduler(subscription_scheduler_task)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://garim.shop",
        "http://www.garim.shop",
        "https://garim.shop",
        "https://www.garim.shop",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(post.router, prefix="/posts")
api_v1.include_router(uploads.router, prefix="/uploads")
api_v1.include_router(oauth.router, prefix="/auth")
api_v1.include_router(setting.router, prefix="/settings")
api_v1.include_router(admin.router, prefix="/admin")
api_v1.include_router(analysis.router, prefix="/analysis")
api_v1.include_router(worker.router, prefix="/worker")
api_v1.include_router(payment.router, prefix="/payment")
api_v1.include_router(subscription.router, prefix="/subscriptions")
api_v1.include_router(report.router, prefix="/reports")
api_v1.include_router(notification.router, prefix="/notifications")

app.include_router(api_v1)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        reload=True,
    )
