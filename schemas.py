import datetime
from pydantic import BaseModel
from typing import Optional

# 型の定義
###models.pyで設計した情報をもとに型を決める

###AttendanceRecord
class AttendanceRecord(BaseModel):
    index: int
    member_id: int
    date: datetime.datetime
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]

    class Config:
      orm_mode = True


###MonthlySummary
class MonthlySummary(BaseModel):
    index: int
    member_id: int
    year_month: str
    total_work_time: Optional[datetime.timedelta]
    work_sessions: Optional[int]

    class Config:
      orm_mode = True