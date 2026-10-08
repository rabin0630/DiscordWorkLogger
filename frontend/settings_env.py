"""Botの設定値(.envから読んだ値と、Discordの初期設定)をまとめる"""
import os
from datetime import timedelta, timezone

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
# 社長のDiscordユーザーID。出退勤の挨拶で社長にメンションする
OWNER_DISCORD_ID: str = os.getenv("OWNER_DISCORD_ID", "")

# 日本時間。日本は夏時間がないので、zoneinfoを使わない
JST = timezone(timedelta(hours=9))

# 初期設定
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

intents = discord.Intents.default()
intents.message_content = True
