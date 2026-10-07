"""get_dbを、テスト用のデータベースにつなぐものに差し替える"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src import config
from src.database import make_database_url

test_engine = create_engine(make_database_url(config.MYSQL_TEST_DATABASE), pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_db() -> Iterator[Session]:
    """テスト用のデータベースのセッションを作り、終わったら閉じる

    Yields:
        Session: テスト用のデータベースのセッション
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
