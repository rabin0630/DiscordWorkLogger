"""BotからAPIを呼ぶための通信の部品"""
import logging
from dataclasses import dataclass

import aiohttp

from settings_env import API_URL, BOT_API_KEY

TIMEOUT = aiohttp.ClientTimeout(total=5)
logger = logging.getLogger(__name__)


class ApiUnavailableError(Exception):
    """APIと通信できない・タイムアウト・500番台の時に投げる"""


class InvalidBotKeyError(ApiUnavailableError):
    """APIが401を返した時に投げる。.envのBOT_API_KEYの設定が間違っている"""


@dataclass
class ApiResponse:
    """APIから返ってきた結果(500番台と401以外)

    Attributes:
        status (int): HTTPのステータスコード。200、400、403、404、409など
        body (dict): レスポンスのJSON。成功なら{"user_name": "Jun"}など、
            エラーなら{"detail": "name_taken"}など。JSONでなければ{}
    """
    status: int
    body: dict


async def post(path: str, payload: dict) -> ApiResponse:
    """APIにPOSTし、結果を返す

    ヘッダーにX-Bot-Keyを付け、5秒でタイムアウトする。
    401以外の400番台は例外にせず、ApiResponseで返す(detailごとのメッセージは各Cogで出し分けるため)。

    Args:
        path (str): APIのパス。"/register_member"のように"/"から書く
        payload (dict): APIに送るデータ。JSONにして送る

    Returns:
        ApiResponse: ステータスコードとレスポンスのJSON

    Raises:
        InvalidBotKeyError: APIが401を返した時(.envのBOT_API_KEYの設定の間違い)
        ApiUnavailableError: 通信できない・タイムアウト・500番台の時

    Examples:

        >>> response = await post("/register_member", {"user_id": 123, "user_name": "Jun"})
        >>> response.status
        200
        >>> response.body
        {'user_name': 'Jun'}
    """
    headers = {"X-Bot-Key": BOT_API_KEY}
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.post(f"{API_URL}{path}", json=payload, headers=headers) as response:
                if response.status == 401:
                    logger.error("APIが401を返した。BotとAPIの.envのBOT_API_KEYが同じか確かめる")
                    raise InvalidBotKeyError(f"status=401 path={path}")
                if response.status >= 500:
                    raise ApiUnavailableError(f"status={response.status}")
                try:
                    body = await response.json(content_type=None)
                except ValueError:
                    body = {}
                if not isinstance(body, dict):
                    body = {}
                return ApiResponse(response.status, body)
    except (aiohttp.ClientError, TimeoutError) as e:
        raise ApiUnavailableError(str(e)) from e
