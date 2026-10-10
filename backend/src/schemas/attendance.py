"""出退勤のAPIのリクエスト・レスポンスの型"""
from datetime import datetime

from pydantic import AwareDatetime, BaseModel


class StartWorkRequest(BaseModel):
    """/start_workのリクエスト

    Attributes:
        user_id (int): 出勤する人のDiscordのユーザーID
        command_at (AwareDatetime): コマンドした時刻。タイムゾーン付き(ないと422)
    """
    user_id: int
    command_at: AwareDatetime


class StartWorkResponse(BaseModel):
    """/start_workのレスポンス

    Attributes:
        user_name (str): 出勤した人の登録名。挨拶に使う
        start_time (datetime): 出勤時刻(丸めた後、タイムゾーンなしの日本時間)
    """
    user_name: str
    start_time: datetime


class StopWorkRequest(BaseModel):
    """/stop_workのリクエスト

    Attributes:
        user_id (int): 退勤する人のDiscordのユーザーID
        command_at (AwareDatetime): コマンドした時刻。タイムゾーン付き(ないと422)
    """
    user_id: int
    command_at: AwareDatetime


class StopWorkResponse(BaseModel):
    """/stop_workのレスポンス

    Attributes:
        user_name (str): 退勤した人の登録名。挨拶に使う
        start_time (datetime): 出勤時刻(丸めた後、タイムゾーンなしの日本時間)
        end_time (datetime): 退勤時刻(丸めた後、タイムゾーンなしの日本時間)
        work_minutes (int): 今回の勤務時間(分)。丸めた後の出勤時刻から退勤時刻まで
    """
    user_name: str
    start_time: datetime
    end_time: datetime
    work_minutes: int
