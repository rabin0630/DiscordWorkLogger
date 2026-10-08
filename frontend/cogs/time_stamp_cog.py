"""/start_workコマンド(出勤の記録)のCog"""
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from services import api_client
from services.api_client import ApiResponse
from settings_env import env_mode, JST, OWNER_DISCORD_ID
from utils import (
    random_choice_format_list_message,
    format_time,
    EMPLOYEE_ONLY_MESSAGES,
    NOT_REGISTERED_MESSAGES,
    STAMP_API_UNAVAILABLE_MESSAGES,
)

index = "" if env_mode == "prod" else "_test"


class Time_Stamp(commands.Cog):
    # 本人と社長のメンションは、make_start_work_replyで先頭に付ける
    START_WORK_COMPLETE_MESSAGES: list[str] = [
        "{name}なのだ！出勤したのだ！今日もよろしくなのだ！(出勤 {start})",
        "{name}が出勤したのだ！今日も一緒に頑張るのだ！(出勤 {start})",
        "おはようなのだ！{name}の出勤をしっかり記録したのだ！(出勤 {start})",
    ]

    ALREADY_WORKING_MESSAGES: list[str] = [
        "もう出勤しているのだ！",
        "出勤はもう記録してあるのだ！そのまま頑張るのだ！",
        "ん？もう出勤中なのだ！",
    ]

    ALREADY_WORKING_LONG_MESSAGES: list[str] = [
        "もう出勤しているのだ！退勤し忘れていたら、社長に伝えるのだ！",
        "まだ前の出勤が続いているのだ！退勤し忘れていたら、社長に伝えるのだ！",
        "出勤中のままなのだ…前に退勤し忘れていたら、社長に伝えてほしいのだ！",
    ]

    def __init__(self, bot):
        self.bot = bot

    # 出勤する
    @app_commands.command(name=f"start_work{index}", description="出勤します")
    @app_commands.guild_only()
    async def start_work_command(self, interaction: discord.Interaction) -> None:
        """出勤を記録し、本人と社長にメンションした挨拶を、サーバーの全員に見える形で返信する

        Args:
            interaction (discord.Interaction): コマンドのinteraction。
                interaction.user.idで出勤する人を、interaction.created_atで出勤時刻を決める
        """
        await interaction.response.defer()
        command_at = interaction.created_at.astimezone(JST)
        payload = {"user_id": interaction.user.id, "command_at": command_at.isoformat()}
        try:
            response = await api_client.post("/start_work", payload)
        except api_client.ApiUnavailableError:
            await interaction.followup.send(random_choice_format_list_message(STAMP_API_UNAVAILABLE_MESSAGES))
            return
        await interaction.followup.send(make_start_work_reply(response, interaction.user.mention))


# /start_workのdetailと、返すメッセージのリスト
START_WORK_ERROR_MESSAGES: dict[str, list[str]] = {
    "employee_only": EMPLOYEE_ONLY_MESSAGES,
    "not_registered": NOT_REGISTERED_MESSAGES,
    "already_working": Time_Stamp.ALREADY_WORKING_MESSAGES,
    "already_working_long": Time_Stamp.ALREADY_WORKING_LONG_MESSAGES,
}


def make_start_work_reply(response: ApiResponse, user_mention: str) -> str:
    """/start_workの結果から、返信の文を作る

    Discordを使わないので、単体テストできる。

    Args:
        response (ApiResponse): /start_workの結果
        user_mention (str): コマンドした人のメンション。interaction.user.mention

    Returns:
        str: ランダムに選んだ返信の文。200の時は、先頭に本人と社長のメンションを付ける。
            表にないdetailの時は、打刻のコマンドで通信できなかった時の文
    """
    if response.status == 200:
        start_time = datetime.fromisoformat(response.body["start_time"])
        message = random_choice_format_list_message(
            Time_Stamp.START_WORK_COMPLETE_MESSAGES,
            name=response.body["user_name"], start=format_time(start_time))
        return f"{user_mention} <@{OWNER_DISCORD_ID}> {message}"

    detail = response.body.get("detail")
    # 422の時はdetailがリストで返ってくるので、文字列の時だけ探す
    messages = START_WORK_ERROR_MESSAGES.get(detail) if isinstance(detail, str) else None
    if messages is None:
        return random_choice_format_list_message(STAMP_API_UNAVAILABLE_MESSAGES)
    return random_choice_format_list_message(messages)
