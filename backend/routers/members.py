from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas
from crud import members as member_crud
from database import get_db
from services import member_service

# メンバー関係のエンドポイントをまとめるルーター
router = APIRouter(tags=["members"])

### ユーザー名登録

@router.post('/register_member')
async def register_member(member: schemas.Member, db: Session = Depends(get_db)):
  # ルールの判断はserviceに任せ、routerは例外をHTTPのステータスコードに変換する
  try:
      result = member_service.register_member(db, member)
  except member_service.MemberIdAlreadyExistsError:
      raise HTTPException(status_code=409, detail="このIDはすでに使われています")
  except member_service.MemberNameAlreadyExistsError:
      raise HTTPException(status_code=409, detail="この名前はすでに使われています")

  return result

@router.post("/get_name")
async def get_name(member : schemas.MemberIdOnly, db: Session = Depends(get_db)):
  # コマンドしたユーザーのuserIDを使用し、データベースにある名前を返す関数
  # もし登録されていない場合はstatus_code=409を返す
  # select
  result = member_crud.get_name_by_userid(db,member)

  if result == "no_name":
    raise HTTPException(status_code=409, detail="名前は登録されていません")

  return result
