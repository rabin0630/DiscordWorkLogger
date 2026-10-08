"""出退勤の記録の読み書き。見つからなければNoneを返し、例外は投げない。コミットもしない"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from src.models import AttendanceRecord


def get_working_record(member_id: int, db: Session) -> AttendanceRecord | None:
    """出勤中の行(end_timeがNULLの行)を探す

    Args:
        member_id (int): DiscordのユーザーID
        db (Session): DBのセッション

    Returns:
        AttendanceRecord | None: 出勤中の行。勤務外ならNone
    """
    return (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.member_id == member_id, AttendanceRecord.end_time.is_(None))
        .first()
    )


def create_record(
    member_id: int, date: date, start_time: datetime, raw_start_time: datetime, db: Session
) -> AttendanceRecord:
    """出勤の行を追加する。db.addだけ行い、コミットしない

    Args:
        member_id (int): DiscordのユーザーID
        date (date): 出勤日。丸めた後の出勤時刻の日付
        start_time (datetime): 丸めた後の出勤時刻
        raw_start_time (datetime): 打刻した本当の出勤時刻
        db (Session): DBのセッション

    Returns:
        AttendanceRecord: 追加した行。end_timeとraw_end_timeはNone
    """
    record = AttendanceRecord(
        member_id=member_id, date=date, start_time=start_time, raw_start_time=raw_start_time)
    db.add(record)
    return record
