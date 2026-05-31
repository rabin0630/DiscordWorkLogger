import asyncio
import os
import discord
from dotenv import load_dotenv

# envファイル取得
load_dotenv()

DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN")
TARGET_GUILD_ID: int = int(os.getenv("TARGET_GUILD_ID"))
TARGET_CHANNEL_ID: int = int(os.getenv("TARGET_CHANNEL_ID"))

# Intents を設定
intents = discord.Intents.default()
intents.messages = True  # メッセージを取得する
intents.message_content = True  # メッセージ内容を取得する

# クライアントを作成
client = discord.Client(intents=intents)

# ユーザーごとのタイマータスクを管理する辞書
active_timer_tasks = {}

async def run_simple_timer(user: discord.User, channel: discord.abc.Messageable, minutes: int):
    try:
        await asyncio.sleep(minutes * 60)
        await channel.send(f"{user.mention} {minutes}分経過しました！")
    except asyncio.CancelledError:
        pass
    finally:
        active_timer_tasks.pop(user.id, None)

async def run_pomodoro_timer(user: discord.User, channel: discord.abc.Messageable):
    try:
        await asyncio.sleep(25 * 60)
        await channel.send(f"{user.mention} 25分経過！作業お疲れ様でした！5分間の休憩に入りましょう☕️")
        await asyncio.sleep(5 * 60)
        await channel.send(f"{user.mention} 5分間の休憩終了です！作業に戻りましょう！")
    except asyncio.CancelledError:
        pass
    finally:
        active_timer_tasks.pop(user.id, None)

@client.event
async def on_ready():
    # 起動時
    print(f"Timer Bot Logged in as {client.user}!")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild.id != TARGET_GUILD_ID:
        return

    # 指定したチャンネルidじゃなければ返す
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # --- タイマーコマンドの処理 ---
    if message.content.startswith("/timer "):
        cmd_parts = message.content.split()
        if len(cmd_parts) >= 2:
            arg = cmd_parts[1]
            if arg == "stop":
                task = active_timer_tasks.get(message.author.id)
                if task:
                    task.cancel()
                    await message.channel.send(f"{message.author.mention} タイマーを停止しました。")
                else:
                    await message.channel.send(f"{message.author.mention} 実行中のタイマーはありません。")
                return
            elif arg.isdigit():
                minutes = int(arg)
                old_task = active_timer_tasks.get(message.author.id)
                if old_task:
                    old_task.cancel()
                
                await message.channel.send(f"{message.author.mention} タイマーを {minutes}分 にセットしました！")
                task = asyncio.create_task(run_simple_timer(message.author, message.channel, minutes))
                active_timer_tasks[message.author.id] = task
                return

    elif message.content == "/pomodoro timer":
        old_task = active_timer_tasks.get(message.author.id)
        if old_task:
            old_task.cancel()
            
        await message.channel.send(f"{message.author.mention} ポモドーロタイマー開始！25分間の作業に集中しましょう！")
        task = asyncio.create_task(run_pomodoro_timer(message.author, message.channel))
        active_timer_tasks[message.author.id] = task
        return

# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
