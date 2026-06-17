import asyncio
import time
import os
import discord
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from timer import Timer

from discord.ext import commands

# envファイル取得
load_dotenv()

# 初期設定
env_mode = os.getenv("ENV")
print(env_mode)
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

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





# ボットを起動
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
