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


class WorkStatusRequest(BaseModel):
    """/work_statusのリクエスト

    Attributes:
        user_id (int): 出勤状況を確認する人のDiscordのユーザーID
        command_at (AwareDatetime): コマンドした時刻。タイムゾーン付き(ないと422)
    """
    user_id: int
    command_at: AwareDatetime


class WorkStatusResponse(BaseModel):
    """/work_statusのレスポンス

    勤務外の時も、start_timeとelapsed_minutesは省かずNoneで返す。

    Attributes:
        is_working (bool): 出勤中ならTrue、勤務外ならFalse
        start_time (datetime | None): 出勤時刻(丸めた後、タイムゾーンなしの日本時間)。勤務外ならNone
        elapsed_minutes (int | None): 今回の出勤で働いている時間(分)。勤務外ならNone
    """
    is_working: bool
    start_time: datetime | None
    elapsed_minutes: int | None
