import asyncio
from asyncio import base_futures
from aiohttp import client_exceptions
from datetime import timedelta
import time
import os
import discord
import gspread
import json
from datetime import datetime
from dotenv import load_dotenv

# envファイル取得
load_dotenv()

DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN")
TARGET_GUILD_ID: int = int(os.getenv("TARGET_GUILD_ID"))
TARGET_CHANNEL_ID: int = int(os.getenv("TARGET_CHANNEL_ID"))


## Intentsを設定していないとイベントが無効されることがある
# Intents を設定
intents = discord.Intents.default()
intents.messages = True  # メッセージを取得する
intents.message_content = True  # メッセージ内容を取得する
intents.voice_states = True 

# クライアントを作成
client = discord.Client(intents=intents)


# 現在時刻を返す関数
def get_current_time() -> str:
    return datetime.now().strftime("%H:%M")

# ユーザーごとのタイマータスクを管理する辞書
active_timer_tasks = {}

async def run_simple_timer(user, channel, minutes: int):
    try:
        await asyncio.sleep(minutes * 60)
        await channel.send(f"{user.mention} {minutes}分経過しました！")
    except asyncio.CancelledError:
        pass
    finally:
        active_timer_tasks.pop(user.id, None)

async def run_pomodoro_timer(user, channel):
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
    guild = client.get_guild(TARGET_GUILD_ID)
    print(guild.name)
    print(guild.text_channels[0].name)
    print(f"Logged in as {client.user}!")
    print(client)


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

    # メッセージ内容に応じてアクションを設定
    action = None
    if "おはよう" in message.content:
        action = "oha1"
    elif "お疲れ" in message.content:
        action = "otu"

    # データが設定されていない場合は終了
    if not action:
        return

    # スプレッドシートに書き込み
    try:
        if action == "oha1":
            time = get_current_time()
            await message.channel.send(f"おはよう！{time}に出勤したよ！{message.author}")
            
        elif action == "otu":
            time = get_current_time()
            await message.channel.send(f"お疲れs！{time}に退勤したよ！")

        await message.add_reaction("✅")  # :white_check_mark:
        print(f"[{message.author.name}] {action} の記録が完了しました。")
    except Exception as e:
        print(f"err: {e}")
        await message.add_reaction("❌")  # :x:

# ユーザーのボイスチャンネル入室時刻を一時保存する辞書
voice_active_users = {}


@client.event
async def on_voice_state_update(member, before, after):
    send_text_channel = client.get_channel(TARGET_CHANNEL_ID)
    
    # --- 出勤の判定（画面共有を開始したとき） ---
    # ボイスチャンネルに入っていて、画面共有が False -> True になったとき
    # かつ、まだ出勤記録がない場合のみ記録する
    if after.channel is not None and not before.self_stream and after.self_stream:
        if member.id not in voice_active_users:
            time_in = get_current_time()
            voice_active_users[member.id] = time_in
            await send_text_channel.send(f"{member}君、おはよう！{time_in}に出勤したよ！")

    # --- 退勤の判定（ボイスチャンネルから退出、または画面共有を終了したとき） ---
    # すでに出勤記録があるユーザーが、
    # ボイスチャンネルから完全に退出した（after.channel is None）か、
    # または、画面共有が True -> False になったとき
    elif member.id in voice_active_users:
        is_checkout = False
        
        # ボイスチャンネルから完全に退出したとき
        if after.channel is None:
            is_checkout = True
        # ボイスチャンネルには残っているが、画面共有を終了したとき
        elif before.self_stream and not after.self_stream:
            is_checkout = True
            
        if is_checkout:
            time_out = get_current_time()
            time_in = voice_active_users.pop(member.id, None)
            await send_text_channel.send(f"{member}君、お疲れ！{time_out}に退勤したよ！（出勤時間: {time_in}）")
    


# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
