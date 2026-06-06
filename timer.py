from database import user
from discord import app_commands
import asyncio
import os
import discord
import datetime
import random
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


class Timer:
    
    TIMER_SET_MESSAGES = [
        "{mention} {minutes}分のタイマーをセットしたのだ！頑張るのだ！",
        "{mention} {minutes}分後に教えるのだ！集中するのだー！",
        "{mention} タイマーセット完了なのだ！{minutes}分後にまた会おうなのだ！",
        "{mention} {minutes}分、ボクがしっかり計っておくのだ！",
        "{mention} よーいスタートなのだ！{minutes}分の勝負なのだ！",
        "{mention} {minutes}分間の集中タイムなのだ！ずんだ餅でも食べながら待つといいのだ！",
        "{mention} {minutes}分後に呼びにくるのだ！ずんだアロー！",
        "{mention} ばっちり{minutes}分でセットしたのだ！ボクに任せるのだ！",
        "{mention} {minutes}分間のミッション開始なのだ！",
        "{mention} タイマーを{minutes}分でセットなのだ！一緒に頑張るのだ！"
    ]

    TIMER_END_MESSAGES = [
        "{mention} {minutes}分経過したのだ！お疲れ様なのだ！",
        "{mention} 時間なのだー！{minutes}分やりきったのだ！",
        "{mention} ピピピピ！{minutes}分経ったのだ！休憩するのだ！",
        "{mention} {minutes}分経過！ずんだ餅でも食べて休むのだ！",
        "{mention} 約束の{minutes}分が経ったのだ！ボクを褒めるのだ！",
        "{mention} お時間なのだ！{minutes}分間よく頑張ったのだ！",
        "{mention} 終了なのだ！{minutes}分のタイマーが鳴っているのだ！",
        "{mention} {minutes}分達成なのだ！次もボクに任せるのだ！",
        "{mention} タイムアップなのだ！{minutes}分間お見事なのだ！",
        "{mention} カンカンカン！{minutes}分経過なのだ！頑張ったのだ！"
    ]

    TIMER_ALREADY_ACTIVE_MESSAGES = [
        "タイマーはすでに起動しているのだ！終わるまで待つのだ！",
        "今はもうタイマーが動いているのだ！焦らないで待つといいのだ！",
        "すでにセット済みだぞ！落ち着いて集中するのだ！",
        "タイマーはもう走っているのだ！止まるまでずんだ餅でも食べてるのだ！",
        "今測っている途中なのだ！上書きはできないのだー！"
    ]

    TIMER_NOT_ACTIVE_MESSAGES = [
        "{mention} タイマーは起動していないのだ！まずはセットするのだ！",
        "{mention} まだタイマーが動いてないみたいなのだ。セットしてほしいのだ！",
        "{mention} 今は何も測ってないのだ！/timer で呼び出すのだ！",
        "{mention} ボクは今お休み中なのだ。時間を指定してセットするのだー！",
        "{mention} 動いてるタイマーは見つからなかったのだ！新しく作るのだ！"
    ]

    TIMER_REMAINING_MESSAGES = [
        "{mention} 残り時間は {minutes}分{seconds}秒なのだ！",
        "{mention} あと {minutes}分{seconds}秒残っているのだ！頑張るのだ！",
        "{mention} 残りは {minutes}分{seconds}秒なのだ！もうちょっとの辛抱なのだ！",
        "{mention} あと {minutes}分{seconds}秒で終わるのだ！ファイトなのだ！",
        "{mention} ボクの計算だと、あと {minutes}分{seconds}秒なのだ！集中するのだー！"
    ]


    active_timer_tasks      :dict           = {} # タイマーを管理する簡易的なデータベース
    # {user_id: {is_active: bool, end_time: datetime, remaining_time: int}}

    sleep_time              : int           = 60 # 1回のループで減らす秒数

    def __init__(self,interaction:discord.Interaction,minutes:int=0):
        self.user            : discord.User                 = interaction.user 
        self.is_active       : bool                         = False
        self.minutes         : int                          = minutes
        self.remaining_time  : int                          = minutes * self.sleep_time
        self.channel         : discord.abc.Messageable      = interaction.channel
        self.interaction     : discord.Interaction          = interaction

    async def register_timer(self,user_id:int,is_active:bool,end_time:datetime,remaining_time:int):
        self.active_timer_tasks[user_id] = {
            "is_active": is_active,
            "end_time": end_time,
            "remaining_time": remaining_time
        }
    
    async def update_remaining_time(self,user_id:int,remaining_time:int):
        self.active_timer_tasks[user_id]["remaining_time"] = remaining_time
        
    async def run(self):
        if self.active_timer_tasks.get(self.user.id):
            message = random.choice(self.TIMER_ALREADY_ACTIVE_MESSAGES)
            await self.interaction.response.send_message(message)
        else:
            self.task = asyncio.create_task(self.start())

    async def  start(self):
        try:
            self.is_active      = True
            self.remaining_time = self.minutes * 60
            self.end_time       = datetime.datetime.now() + datetime.timedelta(minutes=self.minutes)

            await self.register_timer(self.user.id,self.is_active,self.end_time,self.remaining_time)

            message = random.choice(self.TIMER_SET_MESSAGES).format(mention=self.user.mention, minutes=self.minutes)
            await self.interaction.response.send_message(message)

            while self.remaining_time > 0:
                await asyncio.sleep(1)
                self.remaining_time -= 1
                await self.update_remaining_time(self.user.id,self.remaining_time)
            message = random.choice(self.TIMER_END_MESSAGES).format(mention=self.user.mention, minutes=self.minutes)
            await self.channel.send(message)
            
        except asyncio.CancelledError: # tryの中でエラーが起きた場合の処理
            pass
        finally: # tryが成功しても失敗しても最後に必ず実行される処理
            self.active_timer_tasks.pop(self.user.id, None)
    
    async def show(self):
        if not self.active_timer_tasks.get(self.user.id):
            message = random.choice(self.TIMER_NOT_ACTIVE_MESSAGES).format(mention=self.user.mention)
            await self.interaction.response.send_message(message)
            return
            
        remaining_time :int= self.active_timer_tasks[self.user.id]['remaining_time']
        minutes        :int= remaining_time // 60
        seconds        :int= remaining_time % 60
        
        message = random.choice(self.TIMER_REMAINING_MESSAGES).format(mention=self.user.mention, minutes=minutes, seconds=seconds)
        await self.interaction.response.send_message(message)




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



@command.command(name="timer", description="指定された時間のタイマーをセットします")
async def timer_command(interaction: discord.Interaction, minutes:int):
    timer = Timer(interaction=interaction,minutes=minutes)
    
    await timer.run()

@command.command(name="timer_show", description="タイマーを表示します")
async def timer_show(interaction: discord.Interaction):
    timer = Timer(interaction=interaction)
    
    await timer.show()


# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
