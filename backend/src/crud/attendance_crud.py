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


def end_record(record: AttendanceRecord, end_time: datetime, raw_end_time: datetime) -> AttendanceRecord:
    """出勤中の行に退勤時刻を入れる。値を変えるだけで、コミットしない

    recordはセッションから読んだ行なので、db.addしなくても、コミットの時にUPDATEされる。

    Args:
        record (AttendanceRecord): get_working_recordで見つけた出勤中の行
        end_time (datetime): 丸めた後の退勤時刻
        raw_end_time (datetime): 打刻した本当の退勤時刻

    Returns:
        AttendanceRecord: 退勤時刻を入れた行(引数のrecordと同じもの)
    """
    record.end_time = end_time
    record.raw_end_time = raw_end_time
    return record
