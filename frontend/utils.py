"""Botで共通に使う関数とメッセージ"""
import random
from datetime import datetime, timedelta

def random_choice_format_list_message(list_message: list[str], **kwargs) -> str:
    """リストからメッセージをランダムに1つ選び、{name}などを埋めて返す

    Args:
        list_message (list[str]): 選ぶ候補のメッセージ。{name}のような置き換える場所を書ける
        **kwargs: 置き換える場所に入れる値。name="Jun"なら{name}が"Jun"になる

    Returns:
        str: 選んで値を埋めたメッセージ

    Raises:
        IndexError: list_messageが空の時
        KeyError: 選んだメッセージに、kwargsにない置き換える場所がある時

    Examples:

        >>> random_choice_format_list_message(["{name}の登録が完了したのだ！"], name="Jun")
        'Junの登録が完了したのだ！'

    Note:
        kwargsに余分な値があっても無視される。そのため、{name}を使わないメッセージのリストにもnameを渡してよい
    """
    chose_message = random.choice(list_message)
    return chose_message.format(**kwargs)


def format_time(dt: datetime) -> str:
    """時刻を「時:分」の文字列にする。時は0埋めしない

    Args:
        dt (datetime): 表示する時刻

    Returns:
        str: 「9:30」「18:00」のような文字列

    Examples:

        >>> format_time(datetime(2026, 10, 8, 9, 30))
        '9:30'
    """
    return f"{dt.hour}:{dt.minute:02d}"


def format_minutes(minutes: int) -> str:
    """分数を「時間:分」の文字列にする。24時間を超えてもそのまま時間で表す

    Args:
        minutes (int): 表示する分数。0以上

    Returns:
        str: 「8:30」「0:00」「30:00」のような文字列

    Examples:

        >>> format_minutes(510)
        '8:30'
    """
    return f"{minutes // 60}:{minutes % 60:02d}"


def format_start_time(start: datetime, now: datetime) -> str:
    """出勤時刻に、nowの日付から見た日付を付けて「時:分」の文字列にする

    日付だけを比べる。2日以上前の時は「月/日」を付け、年は付けない。

    Args:
        start (datetime): 出勤時刻(丸めた後、日本時間)
        now (datetime): 今の時刻(日本時間)。APIに送ったcommand_atと同じものを使う

    Returns:
        str: 「9:30」「前日21:30」「10/1 21:30」「翌0:00」のような文字列

    Examples:

        >>> format_start_time(datetime(2026, 10, 7, 21, 30), datetime(2026, 10, 8, 12, 40))
        '前日21:30'
    """
    start_date = start.date()
    now_date = now.date()
    if start_date == now_date:
        return format_time(start)
    if start_date == now_date - timedelta(days=1):
        return f"前日{format_time(start)}"
    # ceil_30で進むのは最大30分なので、翌日より後になることはない
    if start_date == now_date + timedelta(days=1):
        return f"翌{format_time(start)}"
    return f"{start.month}/{start.day} {format_time(start)}"



# どのコマンドでも使うメッセージ
## 社長が従業員専用のコマンドを使った時(detail: employee_only)
EMPLOYEE_ONLY_MESSAGES: list[str] = [
    "このコマンドは従業員しか使えないのだ！",
    "ごめんなのだ！このコマンドは従業員専用なのだ！",
    "社長はこのコマンドを使えないのだ！従業員専用なのだ！",
]

## 登録していない人が、登録している人専用のコマンドを使った時(detail: not_registered)
NOT_REGISTERED_MESSAGES: list[str] = [
    "まだ名前が登録されていないのだ！先に/registerで登録するのだ！",
    "ボクの記録にお前の名前がないのだ！先に/registerで登録するのだ！",
    "名前が登録されていないのだ…まずは/registerからよろしくなのだ！",
]

## APIと通信できなかった時(通信エラー、タイムアウト、500番台、想定していないエラー)
API_UNAVAILABLE_MESSAGES: list[str] = [
    "サーバーとつながらなかったのだ…少し待ってからもう一度試してほしいのだ！",
    "うまくサーバーに届かなかったのだ…少し待ってからもう一度お願いするのだ！",
    "サーバーが返事をしてくれないのだ…時間をおいてもう一度試すのだ！",
]

## /start_work、/stop_workでAPIと通信できなかった時。打刻できていないことも伝える
STAMP_API_UNAVAILABLE_MESSAGES: list[str] = [
    "サーバーとつながらなかったのだ…打刻はできていないのだ！少し待ってからもう一度試してほしいのだ！",
    "うまくサーバーに届かなかったのだ…打刻はできていないのだ！少し待ってからもう一度お願いするのだ！",
    "サーバーが返事をしてくれないのだ…打刻はできていないのだ！時間をおいてもう一度試すのだ！",
]
