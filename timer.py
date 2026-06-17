import logging
import os
import asyncio
import random
import datetime
from dotenv import load_dotenv

import logging
from logging import info

import discord
from discord import app_commands , Interaction
from discord.ext import commands

# NOTE
## https://dottrail.codemountains.org/annotation-todo-tree/  アノテーションコメントの説明url
## interaction.response.channel.sendはリクエストに対してのレスポンスとして一回は必要
## 2回目以降のメッセージ送信はinteraction.followup.sendを使用する
## モノステート・パターンという設計パターンを使用しているらしい


# TODO
## classメソッドの入れ替え : 部品などを一番上にして、コマンドで使用するメソッドは一番下がわかりやすいかも
## **kwargsの意味を調べる
## テストコードを調べる

# FIXME

# HACK

# XXX
## pomodoro_timer : 不明

# envファイル取得
load_dotenv()

# 最新のログが1番上に来るようにするカスタムハンドラ
class ReverseFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, max_lines=300):
        super().__init__(filename, mode='a', encoding=encoding, delay=delay)
        self.max_lines = max_lines
        
    def emit(self, record):
        try:
            msg = self.format(record)
            lines = []
            if os.path.exists(self.baseFilename):
                with open(self.baseFilename, 'r', encoding=self.encoding) as f:
                    lines = f.readlines()
            
            lines.insert(0, msg + '\n')
            if len(lines) > self.max_lines:
                lines = lines[:self.max_lines]
                
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                f.writelines(lines)
        except Exception:
            self.handleError(record)

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        ReverseFileHandler("timer_bot.log", encoding="utf-8", max_lines=300), # 逆順かつ最大300行に制限
        logging.StreamHandler() # 今まで通りターミナル（画面）にも出す用
    ]
)

# TEST環境の時は引数TEST_TOKENとTEST_CHANNEL_IDに変更
# (HACK)リファクタリングした方がいい。とてもみにくい
env_mode = os.getenv("ENV")
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))

# 初期設定
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(
    status   = discord.Status.online,
    intents  = intents,
    activity = ACTIVITY
)

# ClientからBotに変更
bot = commands.Bot(
    command_prefix="!", # プレフィックス型コマンド用（helloコマンド等）
    status=discord.Status.online,
    intents=intents,
    activity=ACTIVITY
)

command = app_commands.CommandTree(client)

class Timer(commands.Cog):

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

    TIMER_RESUME_MESSAGES = [
        "{mention} タイマーを再開したのだ！また頑張るのだ！",
        "{mention} カウントダウン再開なのだ！集中するのだー！",
        "{mention} タイマーが再び動き出したのだ！残り時間をチェックするのだ！",
        "{mention} 休憩終わりなのだ！タイマーを再開するのだ！",
        "{mention} リスタートなのだ！あとちょっと頑張るのだ！",
    ]

    # コンストラクタ
    def __init__(self, bot):
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
        self.bot = bot
        self.activated_timer_datas = {}  # タイマーを管理する簡易的なデータベース
        # {user_id: {is_active: bool, remaining_time: int, is_pomodoro: bool, minutes: int, channel: discord.abc.Messageable}}
        self.timer_tasks = {}

    # TODO: グローバルから引っ張ってるから良くない
    index = None if env_mode == "prod" else "_test"
    
    # タイマーを登録する
    async def register_timer(
        self, 
        user_id       : int, 
        is_active     : bool, 
        remaining_time: int, 
        is_pomodoro   : bool,
        minutes       : int,
        channel       : discord.abc.Messageable
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
            "minutes"       : minutes,
            "channel"       : channel
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
        user_timer = self.activated_timer_datas.get(user_id)
        if not user_timer:
            return

        user_timer["remaining_time"] = remaining_time


    # メッセージ出力
    def random_choice_format_list_message(self, list_message: list[str], **kwargs):
        """

        リストからランダムでメッセージを選択し、discordに出力する

        param:
        list_message:list[str]
            メッセージ
        """
        if not list_message:  # リストが空だったら終了
            return print("メッセージが渡されませんでした")

        # メッセージをランダムで選択し、フォーマットして送信する
        message = random.choice(list_message)
        message = message.format(**kwargs)
        return message

    def kill_timer(self, user_id: int):
        """
        エラーが起きた時や、ポーズ、停止など、正常終了以外の場合に呼ばれる
        タイマーを強制終了する
        """
        # タイマーが起動しているかチェック
        if not self.activated_timer_datas.get(user_id):
            return print("タイマーが起動していません")

        self.activated_timer_datas.pop(user_id, None)  # popは指定したキーを辞書から削除する
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel()
        return

    # タイマーを開始する
    async def countdown(self, user_id: int, end_message: list = None):
        """
        タイマーを開始する
        timer_taskで登録された残り時間を元にカウントダウンを実行
        1秒ごとにremaining_timeを減らしていき、データを更新する
        """
        # 0.ユーザーがタイマーを登録しているかチェック
        if not self.activated_timer_datas.get(user_id):
            return print("タイマーが起動していません")
        
        if not end_message:
            return print("終了メッセージが渡されませんでした")
        
        user_timer = self.activated_timer_datas[user_id]
        channel = user_timer["channel"]
        minutes = user_timer["minutes"]
        mention = f"<@{user_id}>"
        
        try:
            print("3までいけた")
            # 2.カウントダウンを実行。時間が0以上で尚且つ、is_activeがTrueの場合のみ実行
            while user_timer["remaining_time"] > 0 and user_timer.get("is_active"):
                print(user_timer["remaining_time"])
                await asyncio.sleep(1)
                user_timer["remaining_time"] -= 1
                await self.update_remaining_time(user_id, user_timer["remaining_time"])  # 辞書のremaining_timeを更新

            if user_timer["remaining_time"] <= 0:
                message = self.random_choice_format_list_message(end_message, mention=mention, minutes=minutes)
                await channel.send(message)
                # 4. タイマーを停止
                self.kill_timer(user_id)
                print("5までいけた")
        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer(user_id)

    # メイン処理 (start_timer相当)
    #(TODO)タイマーが既に起動している時はエラーが出る
    @app_commands.command(name=f"timer{index}", description="指定された時間のタイマーをセットします")
    async def timer_command(self, interaction: discord.Interaction, minutes: int):
        """
        タイマーを起動するためのメイン処理
        1. 既にタイマーが起動しているかチェック
        2. timer_taskにタイマー情報を登録
        3. discordにリアクションメッセージを送信
        4. countdownをバックグラウンドで実行
        """
        logging.info("timerコマンドを使用しました。")
        if minutes < 0:
            return

        user_id = interaction.user.id
        
        # 1.既にタイマーが起動しているかチェック
        logging.info(f"")
        user_timer = self.activated_timer_datas.get(user_id)
        if user_timer:  # すでに起動している場合は終了
            message = self.random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", minutes))
            await interaction.response.send_message(message)
            return
        print("1までいけた")
        try:
            # 2.timer_taskに情報を登録
            is_active = True
            remaining_time = minutes * 60
            is_pomodoro = False
            await self.register_timer(user_id, is_active, remaining_time, is_pomodoro, minutes, interaction.channel)
            print("2までいけた")
            # 3. discordにリアクションメッセージを送信
            message = self.random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=minutes)
            await interaction.response.send_message(message)
            print("3までいけた")
            # 4. countdownをバックグラウンドで実行
            task = asyncio.create_task(self.countdown(user_id, self.TIMER_END_MESSAGES))
            self.timer_tasks[user_id] = task
            print("4までいけた")

        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer(user_id)

    @app_commands.command(name=f"stoptimer{index}", description="タイマーを停止します")
    async def timer_stop(self, interaction: discord.Interaction):
        logging.info("stopコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:  # タイマー起動していない場合
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        message = self.random_choice_format_list_message(self.TIMER_STOP_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
        await interaction.response.send_message(message)
        self.kill_timer(user_id)
        return

    
    # タイマーを一時停止する
    ## FIXME:停止になる
    @app_commands.command(name=f"pausetimer{index}", description="タイマーを一時停止します")
    async def timer_pause(self, interaction: discord.Interaction):
        logging.info("pauseコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:  # タイマー起動していない場合
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        user_timer["is_active"] = False
        message = self.random_choice_format_list_message(self.TIMER_PAUSE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
        await interaction.response.send_message(message)
        return

    # タイマーを表示する
    @app_commands.command(name=f"showtimer{index}", description="タイマーを表示します")
    async def timer_show(self, interaction: discord.Interaction):
        """
        タイマーを表示する
        remaining_time(秒数)を分と秒に変換して表示
        """
        logging.info("showコマンドを使用しました。")
        user_id = interaction.user.id
        # タイマーが起動していない場合はメッセージを出力して終了
        user_timer = self.activated_timer_datas.get(user_id)
        if not user_timer:  # タイマー起動していない場合
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        # タイマーのremaining_timeを分と秒に変換
        remaining_time: int = user_timer["remaining_time"]
        minutes: int = remaining_time // 60
        seconds: int = remaining_time % 60

        # メッセージを送信
        message = self.random_choice_format_list_message(self.TIMER_REMAINING_MESSAGES, mention=interaction.user.mention, minutes=minutes, seconds=seconds)
        await interaction.response.send_message(message)

    # タイマーを再開する
    ## FIXME:タイマー起動中は作動しない
    @app_commands.command(name=f"resume_timer{index}", description="タイマーを再開します")
    async def timer_resume(self, interaction: discord.Interaction):
        logging.info("resumeコマンドを使用しました。")

        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)

        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        # 
        if user_timer["is_active"] == True:
            await interaction.response.send_message("起動中だよ")
            return

        try:
            logging.info(user_timer)
            user_timer["is_active"] = True
            logging.info(user_timer)
            logging.info(f"{self.TIMER_RESUME_MESSAGES}")
            message = self.random_choice_format_list_message(self.TIMER_RESUME_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            logging.info(message)
            task = asyncio.create_task(
                self.countdown(user_id, self.TIMER_END_MESSAGES) 
            )
            logging.info(task)
            self.timer_tasks[user_id] = task
            logging.info(self.timer_tasks)
            await interaction.response.send_message(message)
        except:
            logging.warning("タイマー起動中はresumeコマンドが使用できないのだ")
            await interaction.response.send_message("shit")
        return

    # (TODO)ポモドーロタイマーの実行
    ## まだ動かないので要修正
    @app_commands.command(name=f"pomodorotimer{index}", description="ポモドーロタイマーをセットします")
    async def timer_pomodoro(self, interaction: discord.Interaction, sets: int = 4):
        """
        ポモドーロタイマーを実行する
        作業時間 25分
        休憩時間 5分
        """
        logging.info("pomodoroコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        if user_timer:  # すでに起動している場合は終了
            message = self.random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            await interaction.response.send_message(message)
            return

        # タイマーを起動
        try:
            is_active = True
            remaining_time = 25 * 60
            is_pomodoro = True
            await self.register_timer(
                user_id, is_active, remaining_time, is_pomodoro, 25, interaction.channel
            )

            message = self.random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=25)
            await interaction.response.send_message(message)

            for _ in range(sets):
                await self.countdown(user_id, self.TIMER_END_MESSAGES)
                await self.countdown(user_id, self.TIMER_END_MESSAGES) 
        except asyncio.CancelledError:  # tryの中でエラーが起きた場合の処理
            print("ループが停止したのだ")
            self.kill_timer(user_id)

@bot.event
# 起動時
async def on_ready():
    logging.info(f"Timer Bot Logged in as {bot.user}!") # 確認
    logging.info("起動しました!")

    await bot.add_cog(Timer(bot))

    bot.tree.copy_global_to(guild=discord.Object(id=TARGET_GUILD_ID))
    await bot.tree.sync(guild=discord.Object(id=TARGET_GUILD_ID))

# ボットを起動
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
        
    else:
        logging.warning("DISCORD_TOKEN が .env ファイルに設定されていません。")
