# utils.py
import random

def random_choice_format_list_message(list_message: list[str], **kwargs) -> str:
    """
    リストからランダムでメッセージを選択し、フォーマットして返す関数
    
    @param list_message: 送信メッセージ一覧
    @return: ランダムで選択されてフォーマットされた文章。
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
