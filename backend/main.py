from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import routers


# データベースの初期設定的なやつ
models.Base.metadata.create_all(bind=engine)

# FastAPIを初期設定的なやつ
app = FastAPI()

# CORS設定（他のシステムから通信を受け入れるため）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.router)

