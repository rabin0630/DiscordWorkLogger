"""/start_workの結合テスト"""
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import AttendanceRecord
from tests.conftest import TEST_OWNER_DISCORD_ID
from tests.integration.test_members_api import EMPLOYEE_ID, OTHER_EMPLOYEE_ID, register


def start_work(client: TestClient, headers: dict[str, str], user_id: int, command_at: str):
    """/start_workを呼ぶ

    Args:
        client (TestClient): APIを呼ぶクライアント
        headers (dict[str, str]): リクエストのヘッダー
        user_id (int): 出勤する人のDiscordのユーザーID
        command_at (str): コマンドした時刻。"2026-10-08T09:05:12+09:00"のような文字列

    Returns:
        httpx.Response: APIのレスポンス
    """
    return client.post("/start_work", json={"user_id": user_id, "command_at": command_at}, headers=headers)


# T-14
@pytest.mark.parametrize(
    ("command_at", "start_time", "raw_start_time"),
    [
        ("2026-10-08T09:05:12+09:00", datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 5, 12)),
        ("2026-10-08T09:30:59+09:00", datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 30, 59)),
        ("2026-10-08T23:45:00+09:00", datetime(2026, 10, 9, 0, 0), datetime(2026, 10, 8, 23, 45)),
    ],
)
def test_start_work(
    client: TestClient, db: Session, bot_headers: dict[str, str],
    command_at: str, start_time: datetime, raw_start_time: datetime,
):
    # 丸めた時刻で出勤できる。出勤日は丸めた後の日付になる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = start_work(client, bot_headers, EMPLOYEE_ID, command_at)

    assert response.status_code == 200
    assert response.json() == {"user_name": "Jun", "start_time": start_time.isoformat()}
    record = db.query(AttendanceRecord).one()
    assert record.member_id == EMPLOYEE_ID
    assert record.date == start_time.date()
    assert record.start_time == start_time
    assert record.end_time is None
    assert record.raw_start_time == raw_start_time
    assert record.raw_end_time is None


# T-15
def test_start_work_utc(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # UTCの時刻で送っても、日本時間で記録される
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T00:05:12+00:00")

    assert response.status_code == 200
    assert response.json()["start_time"] == "2026-10-08T09:30:00"
    record = db.query(AttendanceRecord).one()
    assert record.start_time == datetime(2026, 10, 8, 9, 30)
    assert record.raw_start_time == datetime(2026, 10, 8, 9, 5, 12)


# T-16
def test_owner_cannot_start_work(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 社長は出勤できない
    response = start_work(client, bot_headers, TEST_OWNER_DISCORD_ID, "2026-10-08T09:05:12+09:00")

    assert response.status_code == 403
    assert response.json() == {"detail": "employee_only"}
    assert db.query(AttendanceRecord).count() == 0


# T-17
def test_not_registered_cannot_start_work(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 登録していない人は出勤できない
    response = start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:12+09:00")

    assert response.status_code == 404
    assert response.json() == {"detail": "not_registered"}
    assert db.query(AttendanceRecord).count() == 0


# T-18
@pytest.mark.parametrize(
    ("command_at", "detail"),
    [
        ("2026-10-08T14:29:59+09:00", "already_working"),
        ("2026-10-08T14:30:00+09:00", "already_working_long"),
    ],
)
def test_already_working(client: TestClient, db: Session, bot_headers: dict[str, str], command_at: str, detail: str):
    # 出勤中はもう一度出勤できない。丸めた出勤時刻から5時間以上なら、退勤し忘れのエラーになる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = start_work(client, bot_headers, EMPLOYEE_ID, command_at)

    assert response.status_code == 409
    assert response.json() == {"detail": detail}
    assert db.query(AttendanceRecord).count() == 1


# T-19
def test_start_work_after_stop(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 退勤した後は、もう一度出勤できる(/stop_workがないので、退勤済みの行をDBに直接入れる)
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    db.add(AttendanceRecord(
        member_id=EMPLOYEE_ID, date=date(2026, 10, 8),
        start_time=datetime(2026, 10, 8, 9, 30), end_time=datetime(2026, 10, 8, 12, 0)))
    db.commit()

    response = start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T13:05:00+09:00")

    assert response.status_code == 200
    assert response.json()["start_time"] == "2026-10-08T13:30:00"
    db.expire_all()
    records = db.query(AttendanceRecord).order_by(AttendanceRecord.start_time).all()
    assert len(records) == 2
    assert records[1].start_time == datetime(2026, 10, 8, 13, 30)
    assert records[1].end_time is None


# T-20
def test_start_work_while_other_working(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 他の人が出勤中でも出勤できる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    register(client, bot_headers, OTHER_EMPLOYEE_ID, "Ken")
    start_work(client, bot_headers, OTHER_EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:10:00+09:00")

    assert response.status_code == 200
    assert sorted(r.member_id for r in db.query(AttendanceRecord).all()) == sorted([EMPLOYEE_ID, OTHER_EMPLOYEE_ID])


# T-21
def test_start_work_invalid_bot_key(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # X-Bot-Keyが違うと使えない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = start_work(client, {"X-Bot-Key": "wrong-key"}, EMPLOYEE_ID, "2026-10-08T09:05:12+09:00")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_bot_key"}
    assert db.query(AttendanceRecord).count() == 0


# T-22
def test_start_work_naive_command_at(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # タイムゾーンのない時刻は受け付けない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:12")

    assert response.status_code == 422
    assert db.query(AttendanceRecord).count() == 0
