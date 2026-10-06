import os
import discord
from dotenv import load_dotenv


# envファイルを取得
load_dotenv()

env_mode = os.getenv("ENV")
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = os.getenv(f"{env}_GUILD_ID")

API_URL:str = os.getenv("API_BASE_URL")
# APIにBotからのリクエストだと伝えるための合言葉(X-Bot-Keyヘッダーに入れる)
BOT_API_KEY: str = os.getenv("BOT_API_KEY", "")

# 初期設定
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

intents = discord.Intents.default()
intents.message_content = True
