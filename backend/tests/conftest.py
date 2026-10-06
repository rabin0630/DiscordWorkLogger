from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import config
from src.database import Base
from src.dependencies import get_db
from src.main import app
from src.models import Member
from tests.dependencies import TestSessionLocal, get_test_db, test_engine

# テストで共通に使うもの

TEST_BOT_API_KEY = "test-bot-api-key"
TEST_OWNER_DISCORD_ID = 900000000000000000


@pytest.fixture(scope="session", autouse=True)
def create_tables() -> None:
    """テストの前に、テスト用のデータベースにテーブルを作る

    MYSQL_TEST_DATABASEがない時や、本番と同じデータベースの時は、テストを止める(本番のデータを消さないため)。
    """
    if not config.MYSQL_TEST_DATABASE or config.MYSQL_TEST_DATABASE == config.MYSQL_DATABASE:
        pytest.exit("MYSQL_TEST_DATABASEに、本番とは別のテスト用のデータベースを書いてください")
    Base.metadata.create_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clear_tables() -> None:
    """各テストの前に、Member_tableを空にする"""
    with TestSessionLocal() as db:
        db.query(Member).delete()
        db.commit()


@pytest.fixture(autouse=True)
def test_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """BOT_API_KEYとOWNER_DISCORD_IDを、テスト用の決まった値に差し替える

    .envの値に関係なく、同じ結果になるようにするため。
    """
    monkeypatch.setattr(config, "BOT_API_KEY", TEST_BOT_API_KEY)
    monkeypatch.setattr(config, "OWNER_DISCORD_ID", TEST_OWNER_DISCORD_ID)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """get_dbをテスト用のデータベースに差し替えたTestClient

    withを使わないので、lifespan(本番のデータベースへのcreate_all)は動かない。

    Yields:
        TestClient: APIを呼ぶクライアント
    """
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db() -> Iterator[Session]:
    """テスト用のデータベースの中身を確かめるためのセッション

    Yields:
        Session: テスト用のデータベースのセッション
    """
    with TestSessionLocal() as session:
        yield session


@pytest.fixture
def bot_headers() -> dict[str, str]:
    """正しいX-Bot-Keyのヘッダー

    Returns:
        dict[str, str]: {"X-Bot-Key": TEST_BOT_API_KEY}
    """
    return {"X-Bot-Key": TEST_BOT_API_KEY}
