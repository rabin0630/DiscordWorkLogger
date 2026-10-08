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
