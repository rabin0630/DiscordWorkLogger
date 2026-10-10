"""出勤・退勤・出勤状況の処理"""
from datetime import datetime

from sqlalchemy.orm import Session

from src.crud import attendance_crud
from src.exceptions import AppError
from src.models import AttendanceRecord, Member
from src.services.member_service import get_registered_member
from src.services.time_rules import ceil_30, floor_30, minutes_between, to_jst

LONG_WORKING_MINUTES = 5 * 60


def start_work(user_id: int, command_at: datetime, db: Session) -> tuple[Member, AttendanceRecord]:
    """出勤を記録する

    「確認する順番」の表のとおりに確かめてから、出勤の行を追加し、コミットする。
    同時に2回出勤されても2行できないよう、最初にMember_tableのその人の行をロックする。

    Args:
        user_id (int): 出勤する人のDiscordのユーザーID
        command_at (datetime): コマンドした時刻。タイムゾーン付き
        db (Session): DBのセッション

    Returns:
        tuple[Member, AttendanceRecord]: 出勤した人と、追加した出勤の行

    Raises:
        AppError: 出勤できない時。detailは次のどれか
            - employee_only(403): 社長
            - not_registered(404): 登録していない
            - already_working_long(409): 出勤中で、丸めた出勤時刻から5時間以上経っている
            - already_working(409): 出勤中
    """
    # ロックは、このトランザクションで最初のSELECTにする(待った後に、相手がコミットした行を読めるようにするため)
    member = get_registered_member(user_id, db, for_update=True)
    now = to_jst(command_at)

    working_record = attendance_crud.get_working_record(user_id, db)
    if working_record is not None:
        if minutes_between(working_record.start_time, floor_30(now)) >= LONG_WORKING_MINUTES:
            raise AppError(409, "already_working_long")
        raise AppError(409, "already_working")

    start_time = ceil_30(now)
    record = attendance_crud.create_record(user_id, start_time.date(), start_time, now, db)
    db.commit()
    db.refresh(record)
    return member, record


def stop_work(user_id: int, command_at: datetime, db: Session) -> tuple[Member, AttendanceRecord, int]:
    """退勤を記録する

    「確認する順番」の表のとおりに確かめてから、出勤中の行に退勤時刻を入れ、コミットする。
    同時に2回退勤されても後の方が退勤時刻を上書きしないよう、最初にMember_tableのその人の行をロックする。

    Args:
        user_id (int): 退勤する人のDiscordのユーザーID
        command_at (datetime): コマンドした時刻。タイムゾーン付き
        db (Session): DBのセッション

    Returns:
        tuple[Member, AttendanceRecord, int]: 退勤した人と、退勤時刻を入れた行と、勤務時間(分)

    Raises:
        AppError: 退勤できない時。detailは次のどれか
            - employee_only(403): 社長
            - not_registered(404): 登録していない
            - not_working(409): 勤務外
    """
    # ロックは、このトランザクションで最初のSELECTにする(待った後に、相手がコミットした行を読めるようにするため)
    member = get_registered_member(user_id, db, for_update=True)
    now = to_jst(command_at)

    working_record = attendance_crud.get_working_record(user_id, db)
    if working_record is None:
        raise AppError(409, "not_working")

    # 丸めた退勤時刻が出勤時刻より前なら、出勤時刻と同じにする(勤務時間0分)
    end_time = max(floor_30(now), working_record.start_time)
    record = attendance_crud.end_record(working_record, end_time, now)
    db.commit()
    db.refresh(record)
    return member, record, minutes_between(record.start_time, record.end_time)


def work_status(user_id: int, command_at: datetime, db: Session) -> tuple[AttendanceRecord | None, int | None]:
    """出勤状況を確認する

    「確認する順番」の表のとおりに確かめてから、出勤中の行と働いている時間を返す。
    DBを書き換えないので、ロックもコミットもしない。

    Args:
        user_id (int): 出勤状況を確認する人のDiscordのユーザーID
        command_at (datetime): コマンドした時刻。タイムゾーン付き
        db (Session): DBのセッション

    Returns:
        tuple[AttendanceRecord | None, int | None]: 出勤中の行と、働いている時間(分)。
            働いている時間は、コマンドした時刻を切り捨てて、丸めた出勤時刻から計算する。
            勤務外なら(None, None)

    Raises:
        AppError: 確認できない時。detailは次のどれか
            - employee_only(403): 社長
            - not_registered(404): 登録していない
    """
    get_registered_member(user_id, db)
    now = to_jst(command_at)

    working_record = attendance_crud.get_working_record(user_id, db)
    if working_record is None:
        return None, None
    return working_record, minutes_between(working_record.start_time, floor_30(now))
