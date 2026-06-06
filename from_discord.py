from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine

# データベースの初期設定的なやつ
models.Base.metadata.create_all(bind=engine)

# FastAPIを初期設定的なやつ
app = FastAPI()

# CORS設定（他のシステムから通信を受け入れるため）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DBのセッションを取得するやつ。コピペOK
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()



## post

### 1. 出勤打刻
@app.post('/clock_in')
async def create_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_in(db, attendance_record)

### 2. 退勤打刻
@app.post('/clock_out')
async def update_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_out(db, attendance_record)

### 3. タイマースタート
@app.post('/timer_start')
async def timer_start(timer_info: schemas.TimerInfo, db: Session = Depends(get_db)):
  return crud.start_timer(db, timer_info)
