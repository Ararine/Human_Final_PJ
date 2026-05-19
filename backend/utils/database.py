import os

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -----------------------------
# 1. DB 연결
# -----------------------------

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"

# DB 객체 생성
engine = create_engine(
    DATABASE_URL
)

# 세션 관리 설정
SessionLocal = sessionmaker(
    autocommit=False, # 자동 커밋 설정
    autoflush=True,   # commit 이전 데이터를 db에 적용시킬지 여부 설정
    bind=engine
)

# -----------------------------
# 2. DB 세션 주입
# -----------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()