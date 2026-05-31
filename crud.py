import models,schemas
from datetime import datetime
from sqlalchemy import update
from sqlalchemy.orm import Session

# データベースの操作をする

## Create (出勤時)
def stamp_clock_in(db: Session, attendance_record: schemas.AttendanceRecord):
  data_base = models.AttendanceRecords(
    member_id = attendance_record.member_id,
    date = attendance_record.date,
    start_time = attendance_record.start_time
  )
  db.add(data_base)
  db.commit()
  db.refresh(data_base)
  return data_base

## Update (退勤時)
def stamp_clock_out(db: Session, attendance_record: schemas.AttendanceRecord):
    # 今日の出勤記録を探す
    data_base = db.query(models.AttendanceRecords).filter(
        models.AttendanceRecords.member_id == attendance_record.member_id,
        models.AttendanceRecords.date == attendance_record.date
    ).first()

    # もし出勤記録が見つかったら、退勤時間を上書き保存する
    if data_base and data_base.start_time:
        data_base.end_time = attendance_record.end_time
        db.commit()
        db.refresh(data_base)
        return data_base
    return None
