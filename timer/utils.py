# utils.py
import random

def random_choice_format_list_message(list_message: list[str], **kwargs) -> str:
    """
    リストからランダムでメッセージを選択し、フォーマットして返す関数
    
    @param list_message: 送信メッセージ一覧
    @return: ランダムで選択されてフォーマットされた文章。
    """
    message = random.choice(list_message)
    return message.format(**kwargs)

