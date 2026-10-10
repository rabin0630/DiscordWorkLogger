"""/mynameの返信の文(make_myname_reply)の単体テスト"""
import pytest

from cogs.register_cog import MYNAME_ERROR_MESSAGES, Register, make_myname_reply
from services.api_client import ApiResponse
from utils import API_UNAVAILABLE_MESSAGES


# U-14
def test_myname_reply_success():
    # 確認できた時は、登録名を入れた文になる
    reply = make_myname_reply(ApiResponse(200, {"user_name": "Jun"}))

    assert reply in [m.format(name="Jun") for m in Register.YOUR_NAME_MESSAGES]


# U-15
@pytest.mark.parametrize(
    ("status", "detail"),
    [
        (404, "not_registered"),
        (403, "employee_only"),
    ],
)
def test_myname_reply_error(status: int, detail: str):
    # エラーの時はdetailに合わせた文になる
    reply = make_myname_reply(ApiResponse(status, {"detail": detail}))

    assert reply in MYNAME_ERROR_MESSAGES[detail]


# U-16
def test_myname_reply_unknown_detail():
    # 表にないdetail(422など)の時は、通信できなかった時の文になる
    response = ApiResponse(422, {"detail": [{"type": "missing", "loc": ["body", "user_id"]}]})

    reply = make_myname_reply(response)

    assert reply in API_UNAVAILABLE_MESSAGES
