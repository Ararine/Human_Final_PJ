import uvicorn,os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from routes import post

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post.router, prefix="/posts")
if __name__ == "__main__":
    uvicorn.run(
        "main:app",          # 모듈:앱 경로
        host=os.getenv("HOST"), 
        port=int(os.getenv("PORT")),
        reload=True,
    )
