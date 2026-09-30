import models, schemas
from sqlalchemy.orm import Session

from models import Member
# メンバー関係のデータベースの操作をする


### Createをするときの流れ
"""
1. modelsからモデルをimport
2. schemasからモデルをimport
3. Sessionをimport
4. SessionからSession_factoryをimport
5. Session_factoryからsessionをimport
6. models.Base.metadata.create_all(bind=engine)

7. {}.pyから{}_infoをimport
8. {}.pyから{}_infoをimport


"""

## Read (メンバー)
def get_member_by_id(db: Session, user_id: int) -> models.Member | None:
    # user_idでメンバーを探す。見つからない場合はNoneを返す
    return db.query(models.Member).filter(models.Member.user_id == user_id).first()

def get_member_by_name(db: Session, user_name: str) -> models.Member | None:
    # user_nameでメンバーを探す。見つからない場合はNoneを返す
    return db.query(models.Member).filter(models.Member.user_name == user_name).first()

## Create (メンバー)
def create_member(db: Session, member: schemas.Member) -> models.Member:
    # メンバーを登録する。重複チェックはservices/member_service.pyで行う
    data_base = models.Member(
        user_id = member.user_id,
        user_name = member.user_name,
        created_date = member.created_date,
    )
    db.add(data_base)
    db.commit()
    db.refresh(data_base)
    print(data_base)
    return data_base

## get
def get_name_by_userid(db: Session, member: schemas.MemberIdOnly):

    # 送信されたuser_idを用いてnameを取得する
    data_base = db.query(Member).filter(
        Member.user_id == member.user_id
    ).first()

    if data_base is None:
        return "no_name"

    return data_base