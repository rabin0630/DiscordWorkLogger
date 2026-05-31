from sqlalchemy import Column, String, Integer, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class AttendanceRecords(Base):
    __tablename__ = "attendance_records"

    # 1回の出退勤セッションを管理するテーブル。
    # 1行で1回の出退勤セッションを表す。

    index = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    member_id = Column(BigInteger)
    date = Column(DateTime)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)


class MonthlySummary(Base):
    __tablename__ = "monthly_summary"

    # 1ヶ月の勤怠情報を集計して管理するテーブル。
    # 1行で1ヶ月の勤怠情報を表す。

    index = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    member_id = Column(BigInteger)
    year_month = Column(String(6))
    total_work_time = Column(DateTime, nullable=True)
    work_sessions = Column(Integer, nullable=True)
    