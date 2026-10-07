# utils.py
import random

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



# どのコマンドでも使うメッセージ
## 社長が従業員専用のコマンドを使った時(detail: employee_only)
EMPLOYEE_ONLY_MESSAGES: list[str] = [
    "このコマンドは従業員しか使えないのだ！",
    "ごめんなのだ！このコマンドは従業員専用なのだ！",
    "社長はこのコマンドを使えないのだ！従業員専用なのだ！",
]

## APIと通信できなかった時(通信エラー、タイムアウト、500番台、想定していないエラー)
API_UNAVAILABLE_MESSAGES: list[str] = [
    "サーバーとつながらなかったのだ…少し待ってからもう一度試してほしいのだ！",
    "うまくサーバーに届かなかったのだ…少し待ってからもう一度お願いするのだ！",
    "サーバーが返事をしてくれないのだ…時間をおいてもう一度試すのだ！",
]
