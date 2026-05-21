import uvicorn,os,logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from core.logger import setup_logging
from routes import oauth, post, uploads

################## 초기 세팅 ######################
## 로거 기본 세팅
setup_logging()

logger = logging.getLogger(__name__)

logger.info("backend server is running...")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "http://192.168.0.8:3000",  # 김민영
                   "http://192.168.0.20:3000", # 고관홍
                   "http://192.168.0.64:3000", # 강사님
                   "http://192.168.0.65:3000"  # 오세덕
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post.router, prefix="/posts")
app.include_router(uploads.router, prefix="/uploads")
app.include_router(oauth.router, prefix="/auth")
if __name__ == "__main__":
    uvicorn.run(
        "main:app",          # 모듈:앱 경로
        host=os.getenv("HOST"), 
        port=int(os.getenv("PORT")),
        reload=True,
    )
