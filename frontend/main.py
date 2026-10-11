"""Botを起動し、各Cogを読み込んで、コマンドをサーバーに反映する"""
import os
import discord


from dotenv import load_dotenv
from cogs.timer_cog import Timer
from cogs.time_stamp_cog import Time_Stamp
from cogs.register_cog import Register
from cogs.help_cog import Help
from discord.ext import commands

# envファイル取得
load_dotenv()

# 初期設定
env_mode = os.getenv("ENV")
print(env_mode)
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "/helpでコマンドを確認")  # botのステータス

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!", # プレフィックス型コマンド用（helloコマンド等）
    status=discord.Status.online,
    intents=intents,
    activity=ACTIVITY
)

@bot.event
async def on_ready():
    # 起動時
    print(f"Logged in as {bot.user}!")
    await bot.add_cog(Timer(bot))
    await bot.add_cog(Time_Stamp(bot))
    await bot.add_cog(Register(bot))
    await bot.add_cog(Help(bot))

    # グローバルコマンドを特定のサーバーにコピーして即時反映させるのだ！
    target_guild = discord.Object(id=TARGET_GUILD_ID)
    bot.tree.copy_global_to(guild=target_guild)
    await bot.tree.sync(guild=target_guild)
    print("コマンドの即時反映が完了したのだ！")



# ボットを起動
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
