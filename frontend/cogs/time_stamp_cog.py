"""/start_work、/stop_work、/work_statusコマンド(出退勤の記録と出勤状況の確認)のCog"""
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
    format_minutes,
    format_start_time,
    EMPLOYEE_ONLY_MESSAGES,
    NOT_REGISTERED_MESSAGES,
    API_UNAVAILABLE_MESSAGES,
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

    # 本人と社長のメンションは、make_stop_work_replyで先頭に付ける
    STOP_WORK_COMPLETE_MESSAGES: list[str] = [
        "{name}なのだ！退勤したのだ！お疲れさまなのだ！(退勤 {end} / 勤務時間 {work})",
        "{name}が退勤したのだ！今日もよく頑張ったのだ！(退勤 {end} / 勤務時間 {work})",
        "お疲れさまなのだ！{name}の退勤をしっかり記録したのだ！(退勤 {end} / 勤務時間 {work})",
    ]

    NOT_WORKING_MESSAGES: list[str] = [
        "まだ出勤していないのだ！出勤し忘れていたら、社長に伝えるのだ！",
        "出勤の記録がないのだ！出勤し忘れていたら、社長に伝えるのだ！",
        "ん？今は勤務外なのだ…出勤し忘れていたら、社長に伝えてほしいのだ！",
    ]

    WORKING_STATUS_MESSAGES: list[str] = [
        "出勤中なのだ！{start}に出勤して、今{elapsed}働いているのだ！",
        "今は出勤中なのだ！{start}から{elapsed}働いているのだ！その調子なのだ！",
        "{start}に出勤して、今{elapsed}働いているのだ！無理しすぎないようにするのだ！",
    ]

    OFF_WORK_MESSAGES: list[str] = [
        "今は勤務外なのだ！",
        "今は出勤していないのだ！勤務外なのだ！",
        "勤務外なのだ！ゆっくり休むのだ！",
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

    # 退勤する
    @app_commands.command(name=f"stop_work{index}", description="退勤します")
    @app_commands.guild_only()
    async def stop_work_command(self, interaction: discord.Interaction) -> None:
        """退勤を記録し、本人と社長にメンションした挨拶を、サーバーの全員に見える形で返信する

        Args:
            interaction (discord.Interaction): コマンドのinteraction。
                interaction.user.idで退勤する人を、interaction.created_atで退勤時刻を決める
        """
        await interaction.response.defer()
        command_at = interaction.created_at.astimezone(JST)
        payload = {"user_id": interaction.user.id, "command_at": command_at.isoformat()}
        try:
            response = await api_client.post("/stop_work", payload)
        except api_client.ApiUnavailableError:
            await interaction.followup.send(random_choice_format_list_message(STAMP_API_UNAVAILABLE_MESSAGES))
            return
        await interaction.followup.send(make_stop_work_reply(response, interaction.user.mention))

    # 出勤状況を確認する
    @app_commands.command(name=f"work_status{index}", description="自分の出勤状況を確認します")
    @app_commands.guild_only()
    async def work_status_command(self, interaction: discord.Interaction) -> None:
        """出勤状況を、サーバーの全員に見える形で返信する。メンションは付けない

        Args:
            interaction (discord.Interaction): コマンドのinteraction。
                interaction.user.idで確認する人を、interaction.created_atで働いている時間の計算に使う時刻を決める
        """
        await interaction.response.defer()
        command_at = interaction.created_at.astimezone(JST)
        payload = {"user_id": interaction.user.id, "command_at": command_at.isoformat()}
        try:
            response = await api_client.post("/work_status", payload)
        except api_client.ApiUnavailableError:
            await interaction.followup.send(random_choice_format_list_message(API_UNAVAILABLE_MESSAGES))
            return
        await interaction.followup.send(make_work_status_reply(response, command_at))


# /start_workのdetailと、返すメッセージのリスト
START_WORK_ERROR_MESSAGES: dict[str, list[str]] = {
    "employee_only": EMPLOYEE_ONLY_MESSAGES,
    "not_registered": NOT_REGISTERED_MESSAGES,
    "already_working": Time_Stamp.ALREADY_WORKING_MESSAGES,
    "already_working_long": Time_Stamp.ALREADY_WORKING_LONG_MESSAGES,
}

# /stop_workのdetailと、返すメッセージのリスト
STOP_WORK_ERROR_MESSAGES: dict[str, list[str]] = {
    "employee_only": EMPLOYEE_ONLY_MESSAGES,
    "not_registered": NOT_REGISTERED_MESSAGES,
    "not_working": Time_Stamp.NOT_WORKING_MESSAGES,
}

# /work_statusのdetailと、返すメッセージのリスト
WORK_STATUS_ERROR_MESSAGES: dict[str, list[str]] = {
    "employee_only": EMPLOYEE_ONLY_MESSAGES,
    "not_registered": NOT_REGISTERED_MESSAGES,
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


def make_stop_work_reply(response: ApiResponse, user_mention: str) -> str:
    """/stop_workの結果から、返信の文を作る

    Discordを使わないので、単体テストできる。

    Args:
        response (ApiResponse): /stop_workの結果
        user_mention (str): コマンドした人のメンション。interaction.user.mention

    Returns:
        str: ランダムに選んだ返信の文。200の時は、先頭に本人と社長のメンションを付ける。
            表にないdetailの時は、打刻のコマンドで通信できなかった時の文
    """
    if response.status == 200:
        end_time = datetime.fromisoformat(response.body["end_time"])
        message = random_choice_format_list_message(
            Time_Stamp.STOP_WORK_COMPLETE_MESSAGES,
            name=response.body["user_name"], end=format_time(end_time),
            work=format_minutes(response.body["work_minutes"]))
        return f"{user_mention} <@{OWNER_DISCORD_ID}> {message}"

    detail = response.body.get("detail")
    # 422の時はdetailがリストで返ってくるので、文字列の時だけ探す
    messages = STOP_WORK_ERROR_MESSAGES.get(detail) if isinstance(detail, str) else None
    if messages is None:
        return random_choice_format_list_message(STAMP_API_UNAVAILABLE_MESSAGES)
    return random_choice_format_list_message(messages)


def make_work_status_reply(response: ApiResponse, command_at: datetime) -> str:
    """/work_statusの結果から、返信の文を作る

    Discordを使わないので、単体テストできる。

    Args:
        response (ApiResponse): /work_statusの結果
        command_at (datetime): コマンドした時刻(日本時間)。APIに送ったものと同じ。出勤時刻の日付の表示に使う

    Returns:
        str: ランダムに選んだ返信の文。メンションは付けない。
            表にないdetailの時は、通信できなかった時の文(打刻していないので「打刻はできていない」は付けない)
    """
    if response.status == 200:
        if response.body["is_working"]:
            start_time = datetime.fromisoformat(response.body["start_time"])
            return random_choice_format_list_message(
                Time_Stamp.WORKING_STATUS_MESSAGES,
                start=format_start_time(start_time, command_at),
                elapsed=format_minutes(response.body["elapsed_minutes"]))
        return random_choice_format_list_message(Time_Stamp.OFF_WORK_MESSAGES)

    detail = response.body.get("detail")
    # 422の時はdetailがリストで返ってくるので、文字列の時だけ探す
    messages = WORK_STATUS_ERROR_MESSAGES.get(detail) if isinstance(detail, str) else None
    if messages is None:
        return random_choice_format_list_message(API_UNAVAILABLE_MESSAGES)
    return random_choice_format_list_message(messages)
