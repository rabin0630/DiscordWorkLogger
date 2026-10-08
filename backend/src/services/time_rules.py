"""30分単位の出退勤と、時間の計算"""
from datetime import datetime, timedelta

from src import config


def to_jst(dt: datetime) -> datetime:
    """タイムゾーン付きの時刻を、タイムゾーンなしの日本時間にする

    秒より細かい値は切り捨てる(MySQLのDATETIMEは秒までで、保存の時に四捨五入されてしまうため)。

    Args:
        dt (datetime): タイムゾーン付きの時刻

    Returns:
        datetime: タイムゾーンなしの日本時間。DBにそのまま保存できる
    """
    return dt.astimezone(config.JST).replace(tzinfo=None, microsecond=0)


def floor_30(dt: datetime) -> datetime:
    """秒を切り捨ててから、30分単位で切り捨てる(退勤、働いている時間の計算に使う)

    Args:
        dt (datetime): 丸める時刻

    Returns:
        datetime: 30分単位に切り捨てた時刻
    """
    dt = dt.replace(second=0, microsecond=0)
    return dt.replace(minute=dt.minute // 30 * 30)


def ceil_30(dt: datetime) -> datetime:
    """秒を切り捨ててから、30分単位で切り上げる(出勤に使う)。0分と30分はそのまま

    Args:
        dt (datetime): 丸める時刻

    Returns:
        datetime: 30分単位に切り上げた時刻。23:45なら翌日の0:00
    """
    dt = dt.replace(second=0, microsecond=0)
    if dt.minute % 30 == 0:
        return dt
    return dt + timedelta(minutes=30 - dt.minute % 30)


def minutes_between(start: datetime, end: datetime) -> int:
    """startからendまでの分数を返す。マイナスになる場合は0

    Args:
        start (datetime): 始まりの時刻
        end (datetime): 終わりの時刻

    Returns:
        int: 分数(秒は切り捨て)。endがstartより前なら0
    """
    return max(0, int((end - start).total_seconds() // 60))
