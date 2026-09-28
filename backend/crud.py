import models, schemas
from sqlalchemy.orm import Session

from models import Member
# データベースの操作をする


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

## Create (出勤時)
def register_member(db: Session,member: schemas.Member):
    # ① まずIDが被ってないかチェック
    if db.query(models.Member).filter(models.Member.user_id == member.user_id).first():
        return "id_error"
    
    # ② 次に名前が被ってないかチェック
    if db.query(models.Member).filter(models.Member.user_name == member.user_name).first():
        return "name_error"

    # ③ どっちも問題なければここで初めて登録（db.add）する
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


## get
def get_name_by_userid(db: Session, member: schemas.MemberIdOnly):

    # 送信されたuser_idを用いてnameを取得する
    data_base = db.query(Member).filter(
        Member.user_id == member.user_id
    ).first()

    if data_base is None:
        return "no_name"

    return data_base