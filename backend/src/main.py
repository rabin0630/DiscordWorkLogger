from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
import importlib
import pkgutil
import routers


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

# routersフォルダの中のファイルを全て読み込み、エンドポイントを登録する
# ※ routersフォルダに置くファイルには、必ずrouterという名前でAPIRouterを定義する
for module_info in pkgutil.iter_modules(routers.__path__):
    module = importlib.import_module(f"routers.{module_info.name}")
    app.include_router(module.router)

