import asyncio
import time
import os
import discord
import aiohttp
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

# ユーザーごとのタイマータスクを管理する辞書
active_timer_tasks = {}

# 現在時刻を返す関数
def get_current_time() -> str:
    return datetime.now().strftime("%H:%M")


async def run_simple_timer(user:discord.User, channel:discord.abc.Messageable, minutes: int):
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
        action = "clock_in"
    elif "お疲れ" in message.content:
        action = "clock_out"

    # データが設定されていない場合は終了
    if not action:
        return

    # API(FastAPI)に送信してデータベースに書き込み
    try:
        now = datetime.now()
        # APIに送るための「箱」を作成
        data_box = {
            "index": 0,
            "member_id": message.author.id,
            "date": now.strftime("%Y-%m-%d"),
            "start_time": now.isoformat(), # Pydanticのエラーを防ぐため、退勤時も一旦今の時間をダミーで入れる
            "end_time": now.isoformat() if action == "clock_out" else None
        }
        
        API_URL = f"http://127.0.0.1:8000/{action}"
        
        # aiohttpを使ってFastAPIにリクエストを送信
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=data_box) as response:
                if response.status == 200:
                    time_str = now.strftime("%H:%M")
                    if action == "clock_in":
                        await message.channel.send(f"おはよう！{time_str}に出勤したよ！{message.author.mention}")
                    else:
                        await message.channel.send(f"お疲れ様！{time_str}に退勤したよ！{message.author.mention}")
                    await message.add_reaction("✅")
                else:
                    await message.channel.send(f"エラーが発生しました... (ステータスコード: {response.status})")
                    await message.add_reaction("❌")

    except Exception as e:
        print(f"err: {e}")
        await message.add_reaction("❌")

# ユーザーのボイスチャンネル入室時刻を一時保存する辞書
voice_active_users = {}


@client.event
async def on_voice_state_update(member, before, after):
    send_text_channel = client.get_channel(TARGET_CHANNEL_ID)
    
    # --- 出勤の判定（画面共有を開始したとき） ---
    if after.channel is not None and not before.self_stream and after.self_stream:
        if member.id not in voice_active_users:
            now = datetime.now()
            time_in = now.strftime("%H:%M")
            voice_active_users[member.id] = time_in
            
            # APIに送信
            data_box = {
                "index": 0,
                "member_id": member.id,
                "date": now.strftime("%Y-%m-%d"),
                "start_time": now.isoformat(),
                "end_time": None
            }
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post("http://127.0.0.1:8000/clock_in", json=data_box)
            except Exception as e:
                print(f"Voice clock_in api error: {e}")
                
            await send_text_channel.send(f"{member.mention}君、おはよう！{time_in}に出勤したよ！")

    # --- 退勤の判定（ボイスチャンネルから退出、または画面共有を終了したとき） ---
    elif member.id in voice_active_users:
        is_checkout = False
        
        if after.channel is None:
            is_checkout = True
        elif before.self_stream and not after.self_stream:
            is_checkout = True
            
        if is_checkout:
            now = datetime.now()
            time_out = now.strftime("%H:%M")
            time_in = voice_active_users.pop(member.id, None)
            
            # APIに送信
            data_box = {
                "index": 0,
                "member_id": member.id,
                "date": now.strftime("%Y-%m-%d"),
                "start_time": now.isoformat(),
                "end_time": now.isoformat()
            }
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post("http://127.0.0.1:8000/clock_out", json=data_box)
            except Exception as e:
                print(f"Voice clock_out api error: {e}")
                
            await send_text_channel.send(f"{member.mention}君、お疲れ！{time_out}に退勤したよ！（出勤時間: {time_in}）")
    


# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
