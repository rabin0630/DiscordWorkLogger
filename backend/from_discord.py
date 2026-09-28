from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import backend.models as models, backend.schemas as schemas, bot.crud as crud
from backend.database import SessionLocal, engine
from fastapi import HTTPException

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
# TODO
@app.post('/create_clock_in')
async def create_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_in(db, attendance_record)

### 2. 退勤打刻
@app.post('/update_clock_out')
async def update_attendance_record(attendance_record: schemas.AttendanceRecord, db: Session = Depends(get_db)):
  return crud.stamp_clock_out(db, attendance_record)

### ユーザー名登録

@app.post('/register_member')
async def register_member(member: schemas.Member, db: Session = Depends(get_db)):
  result = crud.register_member(db,member)
  print(result)
  
  if result == "id_error":
      raise HTTPException(status_code=409, detail="このIDはすでに使われています")
  elif result == "name_error":
      raise HTTPException(status_code=409, detail="この名前はすでに使われています")
      
  return result

@app.post("/get_name")
async def get_name(member : schemas.MemberIdOnly, db: Session = Depends(get_db)):
  # コマンドしたユーザーのuserIDを使用し、データベースにある名前を返す関数
  # もし登録されていない場合はstatus_code=409を返す
  # select 
  result = crud.get_name_by_userid(db,member)

  if result == "no_name":
    raise HTTPException(status_code=409, detail="名前は登録されていません")

  return result