"""名前のAPIのリクエスト・レスポンスの型"""
from pydantic import BaseModel


class RegisterMemberRequest(BaseModel):
    """/register_memberのリクエスト

    user_nameには長さなどの制限を付けない(付けると422になり、エラーコードを返せないため)。

    Attributes:
        user_id (int): 登録する人のDiscordのユーザーID
        user_name (str): 登録する名前。入力したまま送られてくる
    """
    user_id: int
    user_name: str


class RegisterMemberResponse(BaseModel):
    """/register_memberのレスポンス

    Attributes:
        user_name (str): 登録した名前
    """
    user_name: str
