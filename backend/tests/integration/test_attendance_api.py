"""/start_work、/stop_work、/work_statusの結合テスト"""
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


def stop_work(client: TestClient, headers: dict[str, str], user_id: int, command_at: str):
    """/stop_workを呼ぶ

    Args:
        client (TestClient): APIを呼ぶクライアント
        headers (dict[str, str]): リクエストのヘッダー
        user_id (int): 退勤する人のDiscordのユーザーID
        command_at (str): コマンドした時刻。"2026-10-08T18:10:45+09:00"のような文字列

    Returns:
        httpx.Response: APIのレスポンス
    """
    return client.post("/stop_work", json={"user_id": user_id, "command_at": command_at}, headers=headers)


def work_status(client: TestClient, headers: dict[str, str], user_id: int, command_at: str):
    """/work_statusを呼ぶ

    Args:
        client (TestClient): APIを呼ぶクライアント
        headers (dict[str, str]): リクエストのヘッダー
        user_id (int): 出勤状況を確認する人のDiscordのユーザーID
        command_at (str): コマンドした時刻。"2026-10-08T12:40:30+09:00"のような文字列

    Returns:
        httpx.Response: APIのレスポンス
    """
    return client.post("/work_status", json={"user_id": user_id, "command_at": command_at}, headers=headers)


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


# T-23
@pytest.mark.parametrize(
    ("command_at", "end_time", "raw_end_time", "work_minutes"),
    [
        ("2026-10-08T18:10:45+09:00", datetime(2026, 10, 8, 18, 0), datetime(2026, 10, 8, 18, 10, 45), 510),
        ("2026-10-08T18:30:00+09:00", datetime(2026, 10, 8, 18, 30), datetime(2026, 10, 8, 18, 30), 540),
    ],
)
def test_stop_work(
    client: TestClient, db: Session, bot_headers: dict[str, str],
    command_at: str, end_time: datetime, raw_end_time: datetime, work_minutes: int,
):
    # 丸めた時刻で退勤でき、勤務時間が分かる。出勤の値は変わらない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:12+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, command_at)

    assert response.status_code == 200
    assert response.json() == {
        "user_name": "Jun",
        "start_time": "2026-10-08T09:30:00",
        "end_time": end_time.isoformat(),
        "work_minutes": work_minutes,
    }
    record = db.query(AttendanceRecord).one()
    assert record.end_time == end_time
    assert record.raw_end_time == raw_end_time
    assert record.date == date(2026, 10, 8)
    assert record.start_time == datetime(2026, 10, 8, 9, 30)
    assert record.raw_start_time == datetime(2026, 10, 8, 9, 5, 12)


# T-24
def test_stop_work_utc(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # UTCの時刻で送っても、日本時間で記録される
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:10:45+00:00")

    assert response.status_code == 200
    assert response.json()["end_time"] == "2026-10-08T18:00:00"
    record = db.query(AttendanceRecord).one()
    assert record.end_time == datetime(2026, 10, 8, 18, 0)
    assert record.raw_end_time == datetime(2026, 10, 8, 18, 10, 45)


# T-25
@pytest.mark.parametrize(
    ("start_at", "stop_at", "end_time", "raw_end_time"),
    [
        ("2026-10-08T09:05:00+09:00", "2026-10-08T09:20:00+09:00",
         datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 20)),
        ("2026-10-08T23:45:00+09:00", "2026-10-08T23:50:00+09:00",
         datetime(2026, 10, 9, 0, 0), datetime(2026, 10, 8, 23, 50)),
    ],
)
def test_stop_work_before_start_time(
    client: TestClient, db: Session, bot_headers: dict[str, str],
    start_at: str, stop_at: str, end_time: datetime, raw_end_time: datetime,
):
    # 丸めた退勤時刻が出勤時刻より前なら、退勤時刻を出勤時刻と同じにし、勤務時間0分になる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, start_at)

    response = stop_work(client, bot_headers, EMPLOYEE_ID, stop_at)

    assert response.status_code == 200
    assert response.json()["end_time"] == end_time.isoformat()
    assert response.json()["work_minutes"] == 0
    record = db.query(AttendanceRecord).one()
    assert record.end_time == end_time
    assert record.raw_end_time == raw_end_time


# T-26
def test_stop_work_next_day(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 日をまたいで退勤できる。出勤日は変わらない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T21:05:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-09T06:10:00+09:00")

    assert response.status_code == 200
    assert response.json()["end_time"] == "2026-10-09T06:00:00"
    assert response.json()["work_minutes"] == 510
    record = db.query(AttendanceRecord).one()
    assert record.date == date(2026, 10, 8)
    assert record.end_time == datetime(2026, 10, 9, 6, 0)


# T-27
def test_owner_cannot_stop_work(client: TestClient, bot_headers: dict[str, str]):
    # 社長は退勤できない
    response = stop_work(client, bot_headers, TEST_OWNER_DISCORD_ID, "2026-10-08T18:10:00+09:00")

    assert response.status_code == 403
    assert response.json() == {"detail": "employee_only"}


# T-28
def test_not_registered_cannot_stop_work(client: TestClient, bot_headers: dict[str, str]):
    # 登録していない人は退勤できない
    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    assert response.status_code == 404
    assert response.json() == {"detail": "not_registered"}


# T-29
@pytest.mark.parametrize("worked_before", [False, True])
def test_not_working(client: TestClient, db: Session, bot_headers: dict[str, str], worked_before: bool):
    # 出勤していない時は退勤できない(一度も出勤していない時と、退勤した後)
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    if worked_before:
        start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")
        stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:20:00+09:00")

    assert response.status_code == 409
    assert response.json() == {"detail": "not_working"}
    if worked_before:
        record = db.query(AttendanceRecord).one()
        assert record.end_time == datetime(2026, 10, 8, 18, 0)
        assert record.raw_end_time == datetime(2026, 10, 8, 18, 10)


# T-30
def test_stop_work_while_other_working(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 他の人の出勤中の行は退勤しない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    register(client, bot_headers, OTHER_EMPLOYEE_ID, "Ken")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")
    start_work(client, bot_headers, OTHER_EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    assert response.status_code == 200
    jun = db.query(AttendanceRecord).filter(AttendanceRecord.member_id == EMPLOYEE_ID).one()
    ken = db.query(AttendanceRecord).filter(AttendanceRecord.member_id == OTHER_EMPLOYEE_ID).one()
    assert jun.end_time == datetime(2026, 10, 8, 18, 0)
    assert ken.end_time is None


# T-31
def test_stop_work_twice_a_day(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # 1日に2回出勤・退勤できる。退勤済みの行は変わらない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")
    stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T12:10:00+09:00")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T13:05:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    assert response.status_code == 200
    assert response.json()["start_time"] == "2026-10-08T13:30:00"
    assert response.json()["end_time"] == "2026-10-08T18:00:00"
    assert response.json()["work_minutes"] == 270
    records = db.query(AttendanceRecord).order_by(AttendanceRecord.start_time).all()
    assert len(records) == 2
    assert records[0].end_time == datetime(2026, 10, 8, 12, 0)
    assert records[1].end_time == datetime(2026, 10, 8, 18, 0)


# T-32
def test_stop_work_invalid_bot_key(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # X-Bot-Keyが違うと使えない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = stop_work(client, {"X-Bot-Key": "wrong-key"}, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_bot_key"}
    assert db.query(AttendanceRecord).one().end_time is None


# T-33
def test_stop_work_naive_command_at(client: TestClient, db: Session, bot_headers: dict[str, str]):
    # タイムゾーンのない時刻は受け付けない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:45")

    assert response.status_code == 422
    assert db.query(AttendanceRecord).one().end_time is None


# T-39
@pytest.mark.parametrize(
    ("command_at", "elapsed_minutes"),
    [
        ("2026-10-08T12:40:30+09:00", 180),
        ("2026-10-08T09:30:00+09:00", 0),
        ("2026-10-08T09:59:59+09:00", 0),
    ],
)
def test_work_status_working(
    client: TestClient, db: Session, bot_headers: dict[str, str], command_at: str, elapsed_minutes: int,
):
    # 出勤中なら、丸めた出勤時刻と、切り捨てた今の時刻までの働いている時間が分かる。DBは書き換えない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, command_at)

    assert response.status_code == 200
    assert response.json() == {
        "is_working": True, "start_time": "2026-10-08T09:30:00", "elapsed_minutes": elapsed_minutes}
    record = db.query(AttendanceRecord).one()
    assert record.end_time is None
    assert record.raw_end_time is None


# T-40
@pytest.mark.parametrize("worked_before", [False, True])
def test_work_status_off_work(client: TestClient, bot_headers: dict[str, str], worked_before: bool):
    # 勤務外なら、is_workingがfalseになる(一度も出勤していない時と、退勤した後)
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    if worked_before:
        start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")
        stop_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:10:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T18:20:00+09:00")

    assert response.status_code == 200
    assert response.json() == {"is_working": False, "start_time": None, "elapsed_minutes": None}


# T-41
def test_work_status_before_start_time(client: TestClient, bot_headers: dict[str, str]):
    # 丸めた出勤時刻が、切り捨てた今の時刻より後なら0分になる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T23:45:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T23:50:00+09:00")

    assert response.status_code == 200
    assert response.json()["start_time"] == "2026-10-09T00:00:00"
    assert response.json()["elapsed_minutes"] == 0


# T-42
def test_work_status_next_day(client: TestClient, bot_headers: dict[str, str]):
    # 日をまたいで出勤中でも、働いている時間が分かる
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-07T21:05:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T12:40:00+09:00")

    assert response.status_code == 200
    assert response.json()["start_time"] == "2026-10-07T21:30:00"
    assert response.json()["elapsed_minutes"] == 900


# T-43
def test_work_status_utc(client: TestClient, bot_headers: dict[str, str]):
    # UTCの時刻で送っても、日本時間で計算される
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    start_work(client, bot_headers, EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T03:40:30+00:00")

    assert response.status_code == 200
    assert response.json()["elapsed_minutes"] == 180


# T-44
def test_work_status_while_other_working(client: TestClient, bot_headers: dict[str, str]):
    # 他の人の出勤中の行は見ない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")
    register(client, bot_headers, OTHER_EMPLOYEE_ID, "Ken")
    start_work(client, bot_headers, OTHER_EMPLOYEE_ID, "2026-10-08T09:05:00+09:00")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T12:40:00+09:00")

    assert response.status_code == 200
    assert response.json()["is_working"] is False


# T-45
def test_owner_cannot_work_status(client: TestClient, bot_headers: dict[str, str]):
    # 社長は確認できない
    response = work_status(client, bot_headers, TEST_OWNER_DISCORD_ID, "2026-10-08T12:40:00+09:00")

    assert response.status_code == 403
    assert response.json() == {"detail": "employee_only"}


# T-46
def test_not_registered_cannot_work_status(client: TestClient, bot_headers: dict[str, str]):
    # 登録していない人は確認できない
    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T12:40:00+09:00")

    assert response.status_code == 404
    assert response.json() == {"detail": "not_registered"}


# T-47
def test_work_status_invalid_bot_key(client: TestClient, bot_headers: dict[str, str]):
    # X-Bot-Keyが違うと使えない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = work_status(client, {"X-Bot-Key": "wrong-key"}, EMPLOYEE_ID, "2026-10-08T12:40:00+09:00")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_bot_key"}


# T-48
def test_work_status_naive_command_at(client: TestClient, bot_headers: dict[str, str]):
    # タイムゾーンのない時刻は受け付けない
    register(client, bot_headers, EMPLOYEE_ID, "Jun")

    response = work_status(client, bot_headers, EMPLOYEE_ID, "2026-10-08T12:40:30")

    assert response.status_code == 422
