import os
import logging

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -----------------------------
# .env 로드
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# -----------------------------
# DB 연결
# -----------------------------

logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER", "1team")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1team")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "1team")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("DATABASE_URL =", DATABASE_URL)

# DB 객체 생성
engine = create_engine(
    DATABASE_URL,
    echo=True
)

# 세션 관리 설정
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine
)

# -----------------------------
# DB 세션 주입
# -----------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()