# utils.py
import random

def random_choice_format_list_message(list_message: list[str], **kwargs):
    """
    リストからランダムでメッセージを選択し、フォーマットして返す関数
    """
    message = random.choice(list_message)
    return message.format(**kwargs)

