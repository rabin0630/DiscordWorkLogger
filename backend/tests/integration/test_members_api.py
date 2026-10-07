"""/register_memberと/rename_memberの結合テスト"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Member
from src.services.member_service import today_jst
from tests.conftest import TEST_OWNER_DISCORD_ID

EMPLOYEE_ID = 100000000000000001
OTHER_EMPLOYEE_ID = 100000000000000002


def register(client: TestClient, headers: dict[str, str], user_id: int, user_name: str):
    """/register_memberを呼ぶ

    Args:
        client (TestClient): APIを呼ぶクライアント
        headers (dict[str, str]): リクエストのヘッダー
        user_id (int): 登録する人のDiscordのユーザーID
        user_name (str): 登録する名前

    Returns:
        httpx.Response: APIのレスポンス
    """
    return client.post("/register_member", json={"user_id": user_id, "user_name": user_name}, headers=headers)


# T-01
def test_register_member(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 未登録の従業員が名前を登録できる
    response = register(client, bot_headers, EMPLOYEE_ID, "Jun")

    assert response.status_code == 200
    assert response.json() == {"user_name": "Jun"}
    member = db.query(Member).filter(Member.user_id == EMPLOYEE_ID).one()
    assert member.user_name == "Jun"
    assert member.created_date == today_jst()


# T-02
def test_owner_cannot_register(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 社長は登録できない
    response = register(client, bot_headers, TEST_OWNER_DISCORD_ID, "Boss")

    assert response.status_code == 403
    assert response.json() == {"detail": "employee_only"}
    assert db.query(Member).count() == 0


# T-03
def test_name_taken_ignoring_case(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 大文字・小文字だけ違う名前は、他の人と同じ名前として登録できない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = register(client, bot_headers, OTHER_EMPLOYEE_ID, "jun")

    assert response.status_code == 409
    assert response.json() == {"detail": "name_taken"}
    assert [m.user_name for m in db.query(Member).all()] == ["Jun"]


# T-04
@pytest.mark.parametrize(
    ("user_name", "detail"),
    [
        ("", "name_empty"),
        ("じゅん", "name_not_alpha"),
        ("abcdefghijk", "name_too_long"),
    ],
)
def test_invalid_name(client: TestClient, db: Session, bot_headers: dict[str, str], user_name: str, detail: str):
    # ルールに合わない名前は登録できない
    response = register(client, bot_headers, EMPLOYEE_ID, user_name)

    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    assert db.query(Member).count() == 0


# T-05
def test_invalid_bot_key(client: TestClient, db: Session):
    # X-Bot-Keyが違うと使えない
    response = register(client, {"X-Bot-Key": "wrong-key"}, EMPLOYEE_ID, "Jun")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_bot_key"}
    assert db.query(Member).count() == 0


def rename(client: TestClient, headers: dict[str, str], user_id: int, user_name: str):
    """/rename_memberを呼ぶ

    Args:
        client (TestClient): APIを呼ぶクライアント
        headers (dict[str, str]): リクエストのヘッダー
        user_id (int): 名前を変える人のDiscordのユーザーID
        user_name (str): 変更後の名前

    Returns:
        httpx.Response: APIのレスポンス
    """
    return client.post("/rename_member", json={"user_id": user_id, "user_name": user_name}, headers=headers)


# T-06
def test_rename_member(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 登録している従業員が名前を変更できる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = rename(client, bot_headers, EMPLOYEE_ID, "Ken")

    assert response.status_code == 200
    assert response.json() == {"old_name": "Jun", "new_name": "Ken"}
    member = db.query(Member).filter(Member.user_id == EMPLOYEE_ID).one()
    assert member.user_name == "Ken"
    assert member.created_date == today_jst()


# T-07
def test_rename_only_case(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 大文字・小文字だけを変えられる
    register(client, bot_headers, EMPLOYEE_ID, "jun")

    response = rename(client, bot_headers, EMPLOYEE_ID, "Jun")

    assert response.status_code == 200
    assert response.json() == {"old_name": "jun", "new_name": "Jun"}
    member = db.query(Member).filter(Member.user_id == EMPLOYEE_ID).one()
    assert member.user_name == "Jun"


# T-08
def test_owner_cannot_rename(client: TestClient, bot_headers: dict[str, str]):
    # 社長は変更できない
    response = rename(client, bot_headers, TEST_OWNER_DISCORD_ID, "Boss")

    assert response.status_code == 403
    assert response.json() == {"detail": "employee_only"}


# T-09
def test_not_registered_cannot_rename(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 登録していない人は変更できない
    response = rename(client, bot_headers, EMPLOYEE_ID, "Ken")

    assert response.status_code == 404
    assert response.json() == {"detail": "not_registered"}
    assert db.query(Member).count() == 0


# T-10
@pytest.mark.parametrize(
    ("user_name", "detail"),
    [
        ("", "name_empty"),
        ("じゅん", "name_not_alpha"),
        ("abcdefghijk", "name_too_long"),
    ],
)
def test_rename_invalid_name(client: TestClient, db: Session, bot_headers: dict[str, str], user_name: str, detail: str):
    # ルールに合わない名前には変えられない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = rename(client, bot_headers, EMPLOYEE_ID, user_name)

    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    assert [m.user_name for m in db.query(Member).all()] == ["Jun"]


# T-11
def test_rename_same_name(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 今と同じ名前には変えられない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = rename(client, bot_headers, EMPLOYEE_ID, "Jun")

    assert response.status_code == 409
    assert response.json() == {"detail": "same_name"}
    assert [m.user_name for m in db.query(Member).all()] == ["Jun"]


# T-12
def test_rename_name_taken(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 大文字・小文字だけ違う名前も、他の人と同じ名前として変えられない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    register(client, bot_headers, OTHER_EMPLOYEE_ID, "Ken")

    response = rename(client, bot_headers, OTHER_EMPLOYEE_ID, "jun")

    assert response.status_code == 409
    assert response.json() == {"detail": "name_taken"}
    assert sorted(m.user_name for m in db.query(Member).all()) == ["Jun", "Ken"]


# T-13
def test_rename_invalid_bot_key(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # X-Bot-Keyが違うと使えない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = rename(client, {"X-Bot-Key": "wrong-key"}, EMPLOYEE_ID, "Ken")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_bot_key"}
    assert [m.user_name for m in db.query(Member).all()] == ["Jun"]
