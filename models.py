from sqlalchemy import Column, String, Integer, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# データベースのテーブル設計

class AttendanceRecords(Base):
    """
    1回の出退勤セッションを管理するテーブル。
    1行で1回の出退勤セッションを表す。

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
    __tablename__ = "attendance_records"

    index         = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    member_id     = Column(BigInteger)
    date          = Column(DateTime)
    start_time    = Column(DateTime)
    end_time      = Column(DateTime, nullable=True)


class MonthlySummary(Base):
    """
    1ヶ月分の勤怠情報を集計して管理するテーブル。
    1行で1ヶ月の勤怠情報を表す。

    param:
    index           : int
        主キー。自動採番

    member_id       : int
        メンバーID。外部キーでMemberテーブルを参照
        
    year_month      : str
        年月。2026-06
        
    total_work_time : Optional[datetime.timedelta]
        総労働時間。NULLの場合は未集計
        
    work_sessions   : Optional[int]
        出勤回数。NULLの場合は未集計
    """
    __tablename__   = "monthly_summary"

    index           = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    member_id       = Column(BigInteger)
    year_month      = Column(String(6))
    total_work_time = Column(DateTime, nullable=True)
    work_sessions   = Column(Integer, nullable=True)

class TimerInfo(Base):
    """
    タイマー情報を管理するテーブル。
    1行1レコードで、各メンバーのタイマー情報を保持する

    param:
    member_id       : int
        メンバーID。外部キーでMemberテーブルを参照
        
    is_active       : bool
        タイマーが有効かどうか。Trueの場合は有効、Falseの場合は無効
    end_time        : Optional[datetime.datetime]
        終了時間。2026-06-05 18:00。
    remaining_time  : Optional[int]
        残り秒数。一時停止をした時などに使用。Noneの場合はNULL
    """

    __tablename__   = "timer_info"

    member_id       = Column(BigInteger, primary_key=True, unique=True)
    is_active       = Column(Boolean, default=False)
    end_time        = Column(DateTime)
    remaining_time  = Column(Integer, nullable=True)
    


