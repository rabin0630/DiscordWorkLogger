"""/start_workの返信の文(make_start_work_reply)の単体テスト"""
import pytest

from cogs import time_stamp_cog
from cogs.time_stamp_cog import START_WORK_ERROR_MESSAGES, Time_Stamp, make_start_work_reply
from services.api_client import ApiResponse
from utils import STAMP_API_UNAVAILABLE_MESSAGES

TEST_OWNER_DISCORD_ID = "999"


@pytest.fixture(autouse=True)
def owner_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """社長のIDを、テスト用の決まった値に差し替える(.envの値に関係なく、同じ結果になるようにするため)"""
    monkeypatch.setattr(time_stamp_cog, "OWNER_DISCORD_ID", TEST_OWNER_DISCORD_ID)


# U-07
def test_start_work_reply_success():
    # 出勤できた時は、本人と社長のメンションを付けた挨拶になる
    response = ApiResponse(200, {"user_name": "Jun", "start_time": "2026-10-08T09:30:00"})

    reply = make_start_work_reply(response, "<@1>")

    prefix = f"<@1> <@{TEST_OWNER_DISCORD_ID}> "
    assert reply.startswith(prefix)
    expected = [m.format(name="Jun", start="9:30") for m in Time_Stamp.START_WORK_COMPLETE_MESSAGES]
    assert reply.removeprefix(prefix) in expected


# U-08
@pytest.mark.parametrize(
    ("status", "detail"),
    [
        (409, "already_working"),
        (409, "already_working_long"),
        (404, "not_registered"),
        (403, "employee_only"),
    ],
)
def test_start_work_reply_error(status: int, detail: str):
    # エラーの時はdetailに合わせた文になり、メンションは付かない
    reply = make_start_work_reply(ApiResponse(status, {"detail": detail}), "<@1>")

    assert reply in START_WORK_ERROR_MESSAGES[detail]


# U-09
def test_start_work_reply_unknown_detail():
    # 表にないdetail(422など)の時は、打刻のコマンドで通信できなかった時の文になる
    response = ApiResponse(422, {"detail": [{"type": "timezone_aware", "loc": ["body", "command_at"]}]})

    reply = make_start_work_reply(response, "<@1>")

    assert reply in STAMP_API_UNAVAILABLE_MESSAGES
