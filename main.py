import os
import discord
import gspread
import json
from datetime import datetime
from dotenv import load_dotenv


# envファイル取得
load_dotenv()

DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN")
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID"))
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))

# ユーザー ID と スプレッドシートID のマッピングをロード
with open("user_sheet_mapping.json", "r") as f:
    USER_SHEET_MAPPING = json.load(f)

# gspread のクライアントを準備
gc = None
try:
    gc = gspread.service_account(filename="service_account.json")
except Exception as e:
    print(f"service_account.jsonの読み込みに失敗しました: {e}")

# Intents を設定
intents = discord.Intents.default()
intents.messages = True  # メッセージを取得する
intents.message_content = True  # メッセージ内容を取得する

# クライアントを作成
client = discord.Client(intents=intents)


# 現在時刻を返す関数
def get_current_time() -> str:
    return datetime.now().strftime("%H:%M")


def get_current_sheet(spreadsheet):
    """現在の集計シートを選ぶ"""
    today = datetime.now()
    year_str = str(today.year)[-2:]  # '24'
    month = today.month
    day = today.day

    # 16日以降なら翌月、1日～15日なら今月シートを参照
    target_month = month + 1 if day > 15 else month

    sheet_name = f"{year_str}年{target_month}月"
    return spreadsheet.worksheet(sheet_name)


def get_or_create_today_row(sheet):
    """B列から今日の日付の行を見つける。なければ末尾に作成する。"""
    b_col = sheet.col_values(2)
    today = datetime.now()

    # スプレッドシート上の表記ブレを考慮したパターンの作成
    today_patterns = [
        f"{today.month}/{today.day}",
        f"{today.month:02d}/{today.day:02d}",
        today.strftime("%Y/%m/%d"),
        today.strftime("%Y/%-m/%-d"),
    ]

    for idx, val in enumerate(b_col):
        if not val:
            continue
        for pat in today_patterns:
            if pat in val:
                return idx + 1

    # 見つからなかった場合は末尾に新しい行を作成
    all_records = sheet.get_all_values()
    new_row_idx = len(all_records) + 1

    # B列(2)に今日の日付を書き込む
    new_date_str = f"{today.month}/{today.day}"
    sheet.update_cell(new_row_idx, 2, new_date_str)

    return new_row_idx


def record_checkin(spreadsheet, mode):
    sheet = get_current_sheet(spreadsheet)
    row = get_or_create_today_row(sheet)

    time_str = datetime.now().strftime("%H:%M")
    # D列(4)に mode、E列(5)に時刻
    sheet.update_cell(row, 4, mode)
    sheet.update_cell(row, 5, time_str)


def record_checkout(spreadsheet):
    sheet = get_current_sheet(spreadsheet)
    row = get_or_create_today_row(sheet)

    time_str = datetime.now().strftime("%H:%M")
    # F列(6)に退勤時刻、G列(7)に休憩時間
    sheet.update_cell(row, 6, time_str)
    sheet.update_cell(row, 7, "1:00")


@client.event
async def on_ready():
    # 起動時
    print(f"Logged in as {client.user}!")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild.id != TARGET_GUILD_ID:
        return

    # 指定したチャンネルidじゃなければ返す
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # ユーザー ID に基づいて スプレッドシートID を取得
    user_id = str(message.author.id)  # ユーザー ID を文字列に変換
    sheet_id = USER_SHEET_MAPPING.get(user_id)

    # スプレッドシートID が見つからない場合はスキップ
    if not sheet_id:
        print(f"ユーザー ID {user_id} に対応するスプレッドシートIDが見つかりません。")
        await message.add_reaction("❓")
        return

    if gc is None:
        print(
            "service_account.json が正しく読み込めていません。設定を確認してください。"
        )
        await message.add_reaction("⚠️")
        return

    # メッセージ内容に応じてアクションを設定
    action = None
    if "おはよう" in message.content:
        if "出社" in message.content:
            action = "oha1"
        else:
            action = "oha2"
    elif "お疲れ" in message.content:
        action = "otu"

    # データが設定されていない場合は終了
    if not action:
        return

    # スプレッドシートに書き込み
    try:
        spreadsheet = gc.open_by_key(sheet_id)

        if action == "oha1":
            record_checkin(spreadsheet, "出勤")
            time = get_current_time()
            await message.channel.send(f"おはよう！{time}に出勤したよ！")
        elif action == "oha2":
            record_checkin(spreadsheet, "在宅")
        elif action == "otu":
            record_checkout(spreadsheet)
            time = get_current_time()
            await message.channel.send(f"お疲れ！{time}に退勤したよ！")

        await message.add_reaction("✅")  # :white_check_mark:
        print(f"[{message.author.name}] {action} の記録が完了しました。")
    except Exception as e:
        print(f"err: {e}")
        await message.add_reaction("❌")  # :x:


# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
