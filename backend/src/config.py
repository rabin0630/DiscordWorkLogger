import os
from datetime import timedelta, timezone

from dotenv import load_dotenv

# .envにある情報を読み込む
load_dotenv()

## DBの接続情報
MYSQL_USER: str | None = os.getenv("MYSQL_USER")
MYSQL_PASSWORD: str | None = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST: str | None = os.getenv("MYSQL_HOST")
MYSQL_DATABASE: str | None = os.getenv("MYSQL_DATABASE")
MYSQL_TEST_DATABASE: str | None = os.getenv("MYSQL_TEST_DATABASE")

## 社長のDiscordユーザーID。書いていなければNone
_owner_discord_id = os.getenv("OWNER_DISCORD_ID")
OWNER_DISCORD_ID: int | None = int(_owner_discord_id) if _owner_discord_id else None

## BotからのリクエストだとAPIが確かめるための合言葉
BOT_API_KEY: str | None = os.getenv("BOT_API_KEY")

## 日本時間。日本は夏時間がないので、zoneinfoを使わない
JST = timezone(timedelta(hours=9))
