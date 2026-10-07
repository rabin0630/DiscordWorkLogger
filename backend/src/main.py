"""FastAPIのアプリを作り、ルーターと例外ハンドラーを登録する"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src import models  # noqa: F401  create_allの前にテーブル定義を読み込む
from src.database import Base, engine
from src.exceptions import AppError
from src.routers import members


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """APIの起動時に、テーブルがなければ作る

    Args:
        app (FastAPI): FastAPIのアプリ

    Yields:
        None: ここでAPIが動き、止まる時に戻ってくる
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(members.router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """AppErrorを、HTTPのエラーのレスポンスにする

    Args:
        request (Request): 受け取ったリクエスト
        exc (AppError): servicesなどが投げた例外

    Returns:
        JSONResponse: exc.status_codeのステータスと、{"detail": exc.detail}
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
