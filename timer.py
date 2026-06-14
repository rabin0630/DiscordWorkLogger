import logging
from discord import app_commands
import asyncio
import os
import discord
import datetime
import random
from dotenv import load_dotenv
import logging
from logging import info

# NOTE
## interaction.response.channel.sendはリクエストに対してのレスポンスとして一回は必要
## 2回目以降のメッセージ送信はinteraction.followup.sendを使用する

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("timer_bot.log", encoding="utf-8"), # テキストファイルに保存する用
        logging.StreamHandler() # 今まで通りターミナル（画面）にも出す用
    ]
)

# envファイル取得
load_dotenv()

# TEST環境の時は引数TEST_TOKENとTEST_CHANNEL_IDに変更
#(TODO)リファクタリングした方がいい。とてもみにくい
env_mode = os.getenv("ENV")
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))
TARGET_CHANNEL_ID = int(os.getenv(f"{env}_CHANNEL_ID"))
API_URL: str = os.getenv("API_URL")

# 初期設定
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

class MyIntents(discord.Intents):
    def __init__(self, 
    messages=True, 
    message_content=True, 
    voice_states=True, 
    guilds=True,
    members=False):

        super().__init__()
        self.messages        = messages
        self.voice_states    = voice_states
        self.message_content = message_content
        self.guilds          = guilds
        self.members         = members
intents = MyIntents()

client = discord.Client(
    status   = discord.Status.online,
    intents  = intents,
    activity = ACTIVITY
)
command = app_commands.CommandTree(client)


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
        "{mention} タイマーを{minutes}分でセットなのだ！一緒に頑張るのだ！",
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
        "{mention} カンカンカン！{minutes}分経過なのだ！頑張ったのだ！",
    ]

    TIMER_ALREADY_ACTIVE_MESSAGES = [
        "タイマーはすでに起動しているのだ！終わるまで待つのだ！",
        "今はもうタイマーが動いているのだ！焦らないで待つといいのだ！",
        "すでにセット済みだぞ！落ち着いて集中するのだ！",
        "タイマーはもう走っているのだ！止まるまでずんだ餅でも食べてるのだ！",
        "今測っている途中なのだ！上書きはできないのだー！",
    ]

    TIMER_NOT_ACTIVE_MESSAGES = [
        "{mention} タイマーは起動していないのだ！まずはセットするのだ！",
        "{mention} まだタイマーが動いてないみたいなのだ。セットしてほしいのだ！",
        "{mention} 今は何も測ってないのだ！/timer で呼び出すのだ！",
        "{mention} ボクは今お休み中なのだ。時間を指定してセットするのだー！",
        "{mention} 動いてるタイマーは見つからなかったのだ！新しく作るのだ！",
    ]

    TIMER_REMAINING_MESSAGES = [
        "{mention} 残り時間は {minutes}分{seconds}秒なのだ！",
        "{mention} あと {minutes}分{seconds}秒残っているのだ！頑張るのだ！",
        "{mention} 残りは {minutes}分{seconds}秒なのだ！もうちょっとの辛抱なのだ！",
        "{mention} あと {minutes}分{seconds}秒で終わるのだ！ファイトなのだ！",
        "{mention} ボクの計算だと、あと {minutes}分{seconds}秒なのだ！集中するのだー！",
    ]

    TIMER_STOP_MESSAGES = [
        "{mention} タイマーを停止したのだ！",
        "{mention} 途中で止めるのだ！",
        "{mention} 終了なのだ！",
        "{mention} タイマーを止めるのだ！また今度使うのだ！",
    ]

    TIMER_PAUSE_MESSAGES = [
        "{mention} タイマーを一時停止したのだ！",
        "{mention} 途中で止めるのだ！",
        "{mention} またあとで再開するのだー！",
    ]

    activated_timer_datas: dict = {}  # タイマーを管理する簡易的なデータベース
    # {user_id: {is_active: bool, remaining_time: int}}

    # コンストラクタ
    def __init__(self, interaction: discord.Interaction, minutes: int = 0):
        """
        param:
        minutes:int
        minutesにセットする値

        task:None
        taskにセットする値

        is_active:bool
        is_activeにセットする値

        is_pomodoro:bool
        is_pomodoroにセットする値

        user:discord.User
        userにセットする値

        remaining_time:int
        remaining_timeにセットする値

        interaction:discord.Interaction
        interactionにセットする値

        channel:discord.abc.Messageable
        channelにセットする値
        """
        self.user          : discord.User            = interaction.user
        self.task          : None                    = None
        self.minutes       : int                     = minutes
        self.channel       : discord.abc.Messageable = interaction.channel
        self.is_active     : bool                    = False
        self.is_pomodoro   : bool                    = False
        self.interaction   : discord.Interaction     = interaction
        self.remaining_time: int                     = minutes * 60

    # タイマーを登録する
    async def register_timer(
        self, 
        user_id       : int, 
        is_active     : bool, 
        remaining_time: int, 
        is_pomodoro   : bool,
    ):
        """
        ユーザーIDをキーにして、タイマー情報を辞書に登録する

        param:
        user_id         : int
            ユーザーID
        is_active       : bool
            タイマーが有効かどうか
        remaining_time  : int
            残り時間
        is_pomodoro     : bool
            ポモドーロタイマーかどうか
        """
        self.activated_timer_datas[user_id] = {
            "is_active"     : is_active,
            "is_pomodoro"   : is_pomodoro,
            "remaining_time": remaining_time,
        }

    # 残り時間を更新する
    async def update_remaining_time(self, user_id: int, remaining_time: int):
        """

        既存のタイマーの残り時間を更新する

        param:
        user_id:int
            ユーザーID
        remaining_time:int
            残り時間
        """

        # 既にタイマーが起動しているかチェック
        if not self.activated_timer_datas.get(user_id):
            return

        self.activated_timer_datas[user_id]["remaining_time"] = remaining_time

    # メイン処理
    #(TODO)タイマーが既に起動している時はエラーが出る
    async def run(self, is_pomodoro: bool = False):
        """

        タイマーを起動するためのメイン処理
        1. 既にタイマーが起動しているかチェック
        2. timer_taskにタイマー情報を登録
        3. discordにリアクションメッセージを送信
        4. countdownをバックグラウンドで実行

        """
        # 1.既にタイマーが起動しているかチェック
        print(self.minutes)
        if self.activated_timer_datas.get(self.user.id):  # すでに起動している場合は終了
            message = random.choice(self.TIMER_ALREADY_ACTIVE_MESSAGES)
            await self.interaction.response.send_message(message)
            return
        print("1までいけた")
        try:
            # 2.timer_taskに情報を登録
            self.is_active = True
            await self.register_timer(
                self.user.id, self.is_active, self.remaining_time, self.is_pomodoro
            )
            print("2までいけた")
            # 3. discordにリアクションメッセージを送信
            message = random.choice(self.TIMER_SET_MESSAGES).format(
                mention=self.user.mention, minutes=self.minutes
            )
            await self.interaction.response.send_message(message)
            print("3までいけた")
            # 4. countdownをバックグラウンドで実行
            self.task = asyncio.create_task(self.countdown(self.TIMER_END_MESSAGES))
            print("4までいけた")

        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer()

    # (TODO)ポモドーロタイマーの実行
    ## まだ動かないので要修正
    async def pomodoro_timer(self, sets: int = 4):
        """
        ポモドーロタイマーを実行する
        作業時間 25分
        休憩時間 5分
        """

        if self.activated_timer_datas.get(self.user.id):  # すでに起動している場合は終了
            message = random.choice(self.TIMER_ALREADY_ACTIVE_MESSAGES)
            await self.interaction.response.send_message(message)
            return

        # タイマーを起動
        try:
            self.is_active = True

            await self.register_timer(
                self.user.id, self.is_active, self.remaining_time, self.is_pomodoro
            )

            message = random.choice(self.TIMER_SET_MESSAGES).format(
                mention=self.user.mention, minutes=self.minutes
            )

            for _ in range(sets):
                await self.countdown(25, self.TIMER_END_MESSAGES)
                await self.countdown(5, self.TIMER_END_MESSAGES)
        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer()

    # メッセージ出力
    def select_and_format_message(self, list_message: list[str]):
        """

        リストからランダムでメッセージを選択し、discordに出力する

        param:
        message:list[str]
            メッセージ
        """
        if not list_message:  # リストが空だったら終了
            return print("メッセージが渡されませんでした")

        # メッセージをランダムで選択し、メンションして送信する
        message = random.choice(list_message)
        message = message.format(mention=self.user.mention, minutes=self.minutes)
        return message

    def kill_timer(self):
        """
        エラーが起きた時や、ポーズ、停止など、正常終了以外の場合に呼ばれる
        タイマーを強制終了する
        """
        # タイマーが起動しているかチェック
        if not self.activated_timer_datas.get(self.user.id):
            return print("タイマーが起動していません")

        self.activated_timer_datas.pop(self.user.id)  # popは指定したキーを辞書から削除する
        return

    # タイマーを開始する
    async def countdown(self, end_message: list = None):
        """
        タイマーを開始する
        timer_taskで登録された残り時間を元にカウントダウンを実行
        1秒ごとにremaining_timeを減らしていき、データを更新する


        """
        # 0.ユーザーがタイマーを登録しているかチェック
        if not self.activated_timer_datas.get(self.user.id):
            return print("タイマーが起動していません")
        
        if not end_message:
            return print("終了メッセージが渡されませんでした")
        
        # 1.timer_taskから残り時間を取得
        self.remaining_time = self.activated_timer_datas[self.user.id]["remaining_time"]
        
        try:
            print("3までいけた")
            # 2.カウントダウンを実行。時間が0以上で尚且つ、is_activeがTrueの場合のみ実行
            while self.remaining_time > 0 and self.activated_timer_datas.get(self.user.id).get(
                "is_active"
            ):
                print(self.remaining_time)
                await asyncio.sleep(1)
                self.remaining_time -= 1
                await self.update_remaining_time(
                    self.user.id, self.remaining_time
                )  # 辞書のremaining_timeを更新

            # 3.カウントダウン終了後にメッセージを送信
            message = self.select_and_format_message(end_message)
            print(message)
            await self.channel.send(message)
            print("4までいけた")
            # 4. タイマーを停止
            self.kill_timer()
            print("5までいけた")
        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer()

    # タイマーを表示する
    async def show(self):
        """
        タイマーを表示する
        remaining_time(秒数)を分と秒に変換して表示
        """
        # タイマーが起動していない場合はメッセージを出力して終了
        if not self.activated_timer_datas.get(self.user.id):  # タイマー起動していない場合
            message = self.select_and_format_message(self.TIMER_NOT_ACTIVE_MESSAGES)
            await self.interaction.response.send_message(message)
            return

        # タイマーのremaining_timeを分と秒に変換
        remaining_time: int = self.activated_timer_datas[self.user.id]["remaining_time"]
        minutes: int = remaining_time // 60
        seconds: int = remaining_time % 60

        # メッセージを送信
        message = random.choice(
            self.TIMER_REMAINING_MESSAGES
        )  # この時点で変数を埋めてない
        format_message = message.format(
            mention=self.user.mention, minutes=minutes, seconds=seconds
        )
        await self.interaction.response.send_message(format_message)

    async def stop(self):
        if not self.activated_timer_datas.get(self.user.id):  # タイマー起動していない場合
            message = random.choice(self.TIMER_NOT_ACTIVE_MESSAGES)
            formatted_message = message.format(mention=self.user.mention)
            await self.interaction.response.send_message(formatted_message)
            return

        message = random.choice(self.TIMER_STOP_MESSAGES)
        formatted_message = message.format(mention=self.user.mention)
        await self.interaction.response.send_message(formatted_message)
        self.activated_timer_datas.pop(self.user.id, None)
        return

    # タイマーを一時停止する
    async def pause(self):
        if not self.activated_timer_datas.get(self.user.id):  # タイマー起動していない場合
            await self.interaction.response.send_message(self.TIMER_NOT_ACTIVE_MESSAGES)
            return

        self.activated_timer_datas[self.user.id]["is_active"] = False
        print(self.activated_timer_datas[self.user.id]["is_active"])
        message = random.choice(self.TIMER_PAUSE_MESSAGES).format(
            mention=self.user.mention
        )
        await self.interaction.response.send_message(message)
        return

    # タイマーを再開する
    async def resume(self):
        if not self.activated_timer_datas.get(self.user.id):
            message = random.choice(self.TIMER_NOT_ACTIVE_MESSAGES).format(
                mention=self.user.mention
            )
            await self.interaction.response.send_message(message)
            return

        self.activated_timer_datas[self.user.id]["is_active"] = True
        message = random.choice(self.TIMER_RESUME_MESSAGES).format(
            mention=self.user.mention
        )
        self.task = asyncio.create_task(
            self.start(self.activated_timer_datas[self.user.id]["remaining_time"])
        )
        await self.interaction.response.send_message(message)
        return


@client.event
# 起動時
async def on_ready():
    logging.info(f"Timer Bot Logged in as {client.user}!") # 確認
    logging.info("起動しました!")
    command.copy_global_to(guild=discord.Object(id=TARGET_GUILD_ID))
    await command.sync(guild=discord.Object(id=TARGET_GUILD_ID))


@command.command(name="timer", description="指定された時間のタイマーをセットします")
async def timer_command(interaction: discord.Interaction, minutes: int):
    print(minutes)
    if minutes < 0:
        print("shit")
        return
    timer = Timer(interaction=interaction, minutes=minutes)
    await timer.run()


@command.command(name="timer_show", description="タイマーを表示します")
async def timer_show(interaction: discord.Interaction):
    print("shit")
    timer = Timer(interaction=interaction)

    await timer.show()


@command.command(name="timer_stop", description="タイマーを停止します")
async def timer_stop(interaction: discord.Interaction):
    timer = Timer(interaction=interaction)

    await timer.stop()


@command.command(name="timer_pause", description="タイマーを一時停止します")
async def timer_pause(interaction: discord.Interaction):
    timer = Timer(interaction=interaction)

    await timer.pause()


@command.command(name="timer_pomodoro", description="ポモドーロタイマーをセットします")
async def timer_pomodoro(interaction: discord.Interaction, sets: int = 4):
    timer = Timer(interaction=interaction)
    await timer.pomodoro_timer(sets)


# ボットを起動
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
