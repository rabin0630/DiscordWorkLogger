"""/helpコマンド(コマンドの説明を表示する)のCog"""
import discord
from discord import app_commands
from discord.ext import commands
from settings_env import env_mode


class Help(commands.Cog):
    index = "" if env_mode == "prod" else "_test"

    HELP_MESSAGE: str = """\
【従業員専用】
/register {name} … 名前を登録する
/myname … 登録した名前を確認する
/rename {name} … 登録した名前を変更する
/start_work … 出勤を記録する
/stop_work … 退勤を記録する
/work_status … 自分の出勤状況を確認する
【社長専用】
/all_work_status … 社長以外の全員の出勤状況を確認する
【全員】
/help … コマンドの説明を表示する"""

    def __init__(self, bot):
        self.bot = bot

    # コマンドの説明を返す
    @app_commands.command(name=f"help{index}", description="コマンドの説明を表示します")
    @app_commands.guild_only()
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.HELP_MESSAGE, ephemeral=True)
