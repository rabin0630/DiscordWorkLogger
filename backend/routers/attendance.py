from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db

# 出退勤関係のエンドポイントをまとめるルーター
router = APIRouter(tags=["attendance"])

## post

### 1. 出勤打刻
# TODO
@router.post('/create_clock_in')
async def create_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_in(db, attendance_record)

### 2. 退勤打刻
@router.post('/update_clock_out')
async def update_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_out(db, attendance_record)
