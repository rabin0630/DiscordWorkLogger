from database import user
from discord import app_commands
import asyncio
import os
import discord
import datetime
import aiohttp
from schemas import TimerInfo
from dotenv import load_dotenv

# envファイル取得
load_dotenv()

DISCORD_TOKEN: str     = os.getenv("DISCORD_TOKEN")
TARGET_GUILD_ID: int   = int(os.getenv("TARGET_GUILD_ID"))
TARGET_CHANNEL_ID: int = int(os.getenv("TARGET_CHANNEL_ID"))
API_URL: str           = os.getenv("API_URL")

# 初期設定
class MyIntents(discord.Intents):
    def __init__(self,messages=True,message_content=True,voice_states=True):
        super().__init__()
        self.messages            = messages  # メッセージを取得する
        self.message_content     = message_content  # メッセージ内容を取得する
        self.voice_states        = voice_states 

intents                     = MyIntents()

activity                    = discord.Game("タイマー") # botのステータス
client                  = discord.Client(intents=intents, activity=activity, status=discord.Status.online)
command                 = app_commands.CommandTree(client)




class Base_Model_Timer:
    
    active_timer_tasks      :dict           = {} # タイマーを管理する辞書
    sleep_time              : int           = 60

    def __init__(self,user:discord.User,minutes:int):
        self.user               : discord.User             = user 
        self.is_active          : bool                     = False
        self.minutes            : int                      = minutes
        self.remaining_time     : int                      = minutes * self.sleep_time

    async def  start(self,channel: discord.abc.Messageable):
        try:
            self.is_active = True
            self.remaining_time = self.minutes * self.sleep_time
            self.end_time=datetime.datetime.now() + datetime.timedelta(minutes=self.minutes)

            while self.remaining_time > 0:
                await asyncio.sleep(self.sleep_time)
                self.remaining_time -= self.sleep_time
            await channel.send(f"{self.user.mention} {self.minutes}分経過しました！")
            await client.change_presence(activity=discord.Game(name=f"タイマー"))
        except asyncio.CancelledError: # tryの中でエラーが起きた場合の処理
            pass
        finally: # tryが成功しても失敗しても最後に必ず実行される処理
            Base_Model_Timer.active_timer_tasks.pop(self.user.id, None)




# タイマー関数
async def run_custom_timer(user: discord.User, channel: discord.abc.Messageable, minutes: int):
    try:
        # seconds計算
        second = minutes * 60
        
        while second > 0:
            sleep_time = 60
            await asyncio.sleep(sleep_time)
            second -= sleep_time
        
        await channel.send(f"{user.mention} {minutes}分経過しました！")
        await client.change_presence(activity=discord.Game(name=f"タイマー"))
    except asyncio.CancelledError: # tryの中でエラーが起きた場合の処理
        pass
    finally: # tryが成功しても失敗しても最後に必ず実行される処理
        active_timer_tasks.pop(user.id, None)

# ポモドーロタイマー関数
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




# イベントリスナー

@client.event
# 起動時
async def on_ready():
    print(f"Timer Bot Logged in as {client.user}!")
    command.copy_global_to(guild=discord.Object(id=TARGET_GUILD_ID))
    await command.sync(guild=discord.Object(id=TARGET_GUILD_ID))

# スラッシュコマンドの定義
@command.command(name="hello", description="挨拶を返します")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message("こんにちは！")
    await client.change_presence(activity=discord.Game(name="ステータスメッセージだよ"))


@command.command(name="timer", description="指定された時間のタイマーをセットします")
async def timer_command(interaction: discord.Interaction, minutes:int):
    user = interaction.user # インスタンスのコピー
    
    timer = Base_Model_Timer(user=user,minutes=int(minutes))
    
    if Base_Model_Timer.active_timer_tasks.get(user.id):
        timer.cancel()

    # レスポンス
    await interaction.response.send_message(f"{user.mention} タイマーを {minutes}分 にセットしました！")
    
    # タイマー起動
    ## 辞書にタイマーを起動したことをtaskとして記入。
    task = asyncio.create_task(timer.start(interaction.channel)) 
    Base_Model_Timer.active_timer_tasks[user.id] = task
    


# メッセージ受信時
@client.event
async def on_message(message):
    # botのメッセージは無視
    if message.author.bot:
        return

    # 指定したサーバー以外は無視
    if message.guild.id != TARGET_GUILD_ID:
        return

    # 指定したチャンネル以外は無視
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
                task = asyncio.create_task(run_custom_timer(message.author, message.channel, minutes))
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
