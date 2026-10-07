"""FastAPIのDependsで使う共通の部品(DBのセッション、Botの合言葉の確認)"""
import secrets
from collections.abc import Iterator

from fastapi import Header
from sqlalchemy.orm import Session

from src import config
from src.database import SessionLocal
from src.exceptions import AppError


def get_db() -> Iterator[Session]:
    """リクエストごとにDBのセッションを作り、終わったら閉じる

    Yields:
        Session: DBのセッション
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_bot_key(x_bot_key: str | None = Header(default=None)) -> None:
    """X-Bot-Keyヘッダーが、.envのBOT_API_KEYと同じかを確かめる

    Bot用のrouterすべてに、dependenciesとして付ける。

    Args:
        x_bot_key (str | None): X-Bot-Keyヘッダーの値。ヘッダーがない時はNone

    Raises:
        AppError: 401 invalid_bot_key。ヘッダーがない、値が違う、.envにBOT_API_KEYがない時
    """
    # .envにBOT_API_KEYがない時は、ヘッダーなしのリクエストを通さないよう、必ず断る
    if not config.BOT_API_KEY:
        raise AppError(401, "invalid_bot_key")

    if x_bot_key is None:
        raise AppError(401, "invalid_bot_key")

    # 英字以外が入っていてもTypeErrorにならないよう、bytesにして比べる
    if not secrets.compare_digest(x_bot_key.encode(), config.BOT_API_KEY.encode()):
        raise AppError(401, "invalid_bot_key")
