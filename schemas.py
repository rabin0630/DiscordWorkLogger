import datetime
from pydantic import BaseModel
from typing import Optional

# 型の定義
###models.pyで設計した情報をもとに型を決める

"""各テーブルのdocsを書くときのテンプレ。コピペ用として使用
<テーブルの簡単な説明。1行から3行に収める>

param:<各カラムの説明。それぞれのカラムについて説明する>
<カラム>:<カラムの型>
<カラムの簡単な説明>
"""

class AttendanceRecord(BaseModel):
    """ 
    出退勤を管理するテーブル
    1行で1回の出退勤セッションを表す

    param:
    index          : int
        主キー。自動採番
    member_id      : int
        メンバーID。外部キーでMemberテーブルを参照
    date           : datetime.datetime
        日付。2026-06-05
    start_time     : datetime.datetime
        開始時間。2026-06-05 09:00
    end_time       : Optional[datetime.datetime]
        終了時間。2026-06-05 18:00。未設定の場合はNULL
    """
    index          : int
    member_id      : int
    date           : datetime.datetime
    start_time     : datetime.datetime
    end_time       : Optional[datetime.datetime]

    class Config:
      orm_mode = True

class MonthlySummary(BaseModel):
    """
    1ヶ月分の勤怠情報を集約するテーブル
    
    1行で1人の1ヶ月分の勤怠情報を表す

    param:
    index          : int
        主キー。自動採番
    member_id      : int
        メンバーID。外部キーでMemberテーブルを参照
    year_month     : str
        年月。2026-06
    total_work_time: Optional[datetime.timedelta]
        総労働時間。2026-06-05
    work_sessions  : Optional[int]
        出勤回数。2026-06-05 09:00
    """
    index          : int
    member_id      : int
    year_month     : str
    total_work_time: Optional[datetime.timedelta]
    work_sessions  : Optional[int]

    class Config:
      orm_mode = True

class TimerInfo(BaseModel):
    """
    タイマー情報のテーブル
    各メンバーのタイマー情報を保持する

    param:
    member_id      : int
        メンバーID。外部キーでMemberテーブルを参照
    is_active       : bool
        タイマーが有効かどうか。Trueの場合は有効、Falseの場合は無効
    end_time        : Optional[datetime.datetime]
        終了時間。2026-06-05 18:00。未設定の場合はNULL
    """
    member_id     : int
    is_active     : bool
    end_time      : Optional[datetime.datetime]

    class Config:
      orm_mode = True