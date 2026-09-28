from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db

router = APIRouter()

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

### ユーザー名登録

@router.post('/register_member')
async def register_member(member: schemas.Member, db: Session = Depends(get_db)):
  result = crud.register_member(db,member)
  print(result)
  
  if result == "id_error":
      raise HTTPException(status_code=409, detail="このIDはすでに使われています")
  elif result == "name_error":
      raise HTTPException(status_code=409, detail="この名前はすでに使われています")
      
  return result

@router.post("/get_name")
async def get_name(member : schemas.MemberIdOnly, db: Session = Depends(get_db)):
  # コマンドしたユーザーのuserIDを使用し、データベースにある名前を返す関数
  # もし登録されていない場合はstatus_code=409を返す
  # select 
  result = crud.get_name_by_userid(db,member)

  if result == "no_name":
    raise HTTPException(status_code=409, detail="名前は登録されていません")

  return result