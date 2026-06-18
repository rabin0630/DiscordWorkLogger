import time
from datetime import datetime
import asyncio
import random
import datetime
from settings_env import env_mode
from utils import random_choice_format_list_message

import logging
import time
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands


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
        self.activated_timer_data = {}  # タイマーをメモリで管理する簡易的なデータベース
        self.timer_tasks = {}

    # TODO: グローバルから引っ張ってるから良くない
    index = "" if env_mode == "prod" else "_test"
    
    # タイマーを登録する
    async def register_timer(
        self, 
        user_id       : int, 
        is_active     : bool, 
        end_time      : float, 
        remaining_time: float, # pauseコマンドを使用したときに格納する
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
        remaining_time  : float
            残り時間
        is_pomodoro     : bool
            ポモドーロタイマーかどうか
        """
        self.activated_timer_data[user_id] = {
            "is_active"     : is_active,
            "is_pomodoro"   : is_pomodoro,
            "end_time"      : end_time,
            "remaining_time": remaining_time,
            "minutes"       : minutes,
            "channel"       : channel
        }


    def kill_timer(self, user_id: int):
        """
        エラーが起きた時や、ポーズ、停止など、正常終了以外の場合に呼ばれる
        タイマーを強制終了する
        """
        if not self.activated_timer_data.get(user_id):
            return print("タイマーが起動していません")
        self.activated_timer_data.pop(user_id, None)
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel()
        return

    # タイマーを開始する
    async def countdown(self, user_id: int, end_message: list = None):
        """
        タイマーを開始する
        timer_taskで登録された残り時間を元にカウントダウンを実行
        終了予定時刻（end_time）まで一気にスリープして待機する
        """
        if not self.activated_timer_data.get(user_id):
            return print("タイマーが起動していません")
        
        if not end_message:
            return print("終了メッセージが渡されませんでした")
        
        user_timer = self.activated_timer_data[user_id]
        channel = user_timer["channel"]
        minutes = user_timer["minutes"]
        mention = f"<@{user_id}>"
        
        try:
            # 2.カウントダウンを実行（終了時刻まで一気に待機する）
            sleep_time = user_timer["end_time"] - time.time()
            if sleep_time > 0 and user_timer.get("is_active"):
                await asyncio.sleep(sleep_time)

            # スリープから目覚めた時、is_activeがTrueなら終了メッセージを送る
            if user_timer.get("is_active"):
                message = random_choice_format_list_message(end_message, mention=mention, minutes=minutes)
                await channel.send(message)
                self.kill_timer(user_id)
                
        except asyncio.CancelledError:
            # task.cancel()が呼ばれた場合
            user_timer = self.activated_timer_data.get(user_id)
            if user_timer and not user_timer.get("is_active"):
                logging.info(f"タイマーが一時停止(pause)されました: user_id={user_id}")
            else:
                logging.info(f"タイマーが停止(stop)またはエラーによりキャンセルされました: user_id={user_id}")
                self.kill_timer(user_id)

    # ログ出力用の共通処理
    def log_delay(self, interaction: discord.Interaction, command_name: str) -> float:
        front_time = interaction.created_at.timestamp()
        back_time = time.time()
        delay = back_time - front_time
        logging.info(f"[{command_name}] バックエンド到達時刻: {datetime.fromtimestamp(back_time).strftime('%H:%M:%S.%f')}")
        logging.info(f"[{command_name}] フロントエンドから {delay:.3f} 秒遅延して反映されました。")
        return front_time

    # メイン処理 (start_timer相当)
    @app_commands.command(name=f"timer{index}", description="指定された時間のタイマーをセットします")
    async def timer_command(self, interaction: discord.Interaction, minutes: int):
        """
        タイマーを起動するためのメイン処理
        1. 既にタイマーが起動しているかチェック
        2. timer_taskにタイマー情報を登録
        3. discordにリアクションメッセージを送信
        4. countdownをバックグラウンドで実行
        """
        front_time = self.log_delay(interaction, "timer_command")
        if minutes < 0:
            return

        user_id = interaction.user.id
        
        # 1.既にタイマーが起動しているかチェック
        user_timer = self.activated_timer_data.get(user_id)
        if user_timer:
            message = random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", minutes))
            await interaction.response.send_message(message)
            return

        try:
            # 2.timer_taskに情報を登録
            is_active = True
            end_time = front_time + (minutes * 60) # interaction.created_atを基準に計算
            remaining_time = 0.0
            is_pomodoro = False
            await self.register_timer(user_id, is_active, end_time, remaining_time, is_pomodoro, minutes, interaction.channel)
            
            # 3. discordにリアクションメッセージを送信
            message = random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=minutes)
            await interaction.response.send_message(message)
            
            # 4. countdownをバックグラウンドで実行
            task = asyncio.create_task(self.countdown(user_id, self.TIMER_END_MESSAGES))
            self.timer_tasks[user_id] = task

        except Exception as e:
            logging.error(f"Error in timer_command: {e}")
            self.kill_timer(user_id)

    @app_commands.command(name=f"stoptimer{index}", description="タイマーを停止します")
    async def timer_stop(self, interaction: discord.Interaction):
        self.log_delay(interaction, "timer_stop")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)
        
        if not user_timer:
            message = random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        message = random_choice_format_list_message(self.TIMER_STOP_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
        await interaction.response.send_message(message)
        self.kill_timer(user_id)
        return

    # タイマーを一時停止する
    @app_commands.command(name=f"pausetimer{index}", description="タイマーを一時停止します")
    async def timer_pause(self, interaction: discord.Interaction):
        front_time = self.log_delay(interaction, "timer_pause")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)
        
        if not user_timer:
            message = random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        if not user_timer["is_active"]:
            await interaction.response.send_message("すでに一時停止中なのだ！")
            return

        user_timer["is_active"] = False
        # フロントでボタンが押された時間基準で、残り時間を保存する
        user_timer["remaining_time"] = user_timer["end_time"] - front_time
        
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel() # カウントダウンを一時停止
            
        message = random_choice_format_list_message(self.TIMER_PAUSE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
        await interaction.response.send_message(message)
        return

    # タイマーを表示する
    @app_commands.command(name=f"showtimer{index}", description="タイマーを表示します")
    async def timer_show(self, interaction: discord.Interaction):
        """
        タイマーを表示する
        remaining_time(秒数)を分と秒に変換して表示
        """
        self.log_delay(interaction, "timer_show")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)
        
        if not user_timer:
            message = random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        # 残り時間を計算
        if user_timer["is_active"]:
            remaining_time = user_timer["end_time"] - time.time()
        else:
            remaining_time = user_timer["remaining_time"]

        if remaining_time < 0:
            remaining_time = 0

        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)

        message = random_choice_format_list_message(self.TIMER_REMAINING_MESSAGES, mention=interaction.user.mention, minutes=minutes, seconds=seconds)
        await interaction.response.send_message(message)

    # タイマーを再開する
    @app_commands.command(name=f"resume_timer{index}", description="タイマーを再開します")
    async def timer_resume(self, interaction: discord.Interaction):
        front_time = self.log_delay(interaction, "timer_resume")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)

        if not user_timer:
            message = random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        if user_timer["is_active"] == True:
            await interaction.response.send_message("起動中だよ")
            return

        try:
            user_timer["is_active"] = True
            # 新しい終了時刻を計算
            user_timer["end_time"] = front_time + user_timer["remaining_time"]
            user_timer["remaining_time"] = 0.0

            message = random_choice_format_list_message(self.TIMER_RESUME_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            
            task = asyncio.create_task(
                self.countdown(user_id, self.TIMER_END_MESSAGES) 
            )
            self.timer_tasks[user_id] = task
            await interaction.response.send_message(message)
        except Exception as e:
            logging.warning(f"タイマー起動中はresumeコマンドが使用できないのだ: {e}")
            await interaction.response.send_message("shit")
        return

    # ポモドーロタイマーの実行
    @app_commands.command(name=f"pomodorotimer{index}", description="ポモドーロタイマーをセットします")
    async def timer_pomodoro(self, interaction: discord.Interaction, sets: int = 4):
        """
        ポモドーロタイマーを実行する
        作業時間 25分
        休憩時間 5分
        """
        front_time = self.log_delay(interaction, "timer_pomodoro")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)

        if user_timer:
            message = random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            await interaction.response.send_message(message)
            return

        try:
            is_active = True
            end_time = front_time + (25 * 60)
            is_pomodoro = True
            await self.register_timer(
                user_id, is_active, end_time, 0.0, is_pomodoro, 25, interaction.channel
            )

            message = random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=25)
            await interaction.response.send_message(message)

            for _ in range(sets):
                # 作業25分 (登録済みなのでそのまま待つ)
                await self.countdown(user_id, self.TIMER_END_MESSAGES)
                
                # 休憩5分 (新しくend_timeをセット)
                user_timer = self.activated_timer_data.get(user_id)
                if not user_timer:
                    break
                user_timer["is_active"] = True
                user_timer["end_time"] = time.time() + (5 * 60)
                user_timer["minutes"] = 5
                await self.countdown(user_id, self.TIMER_END_MESSAGES) 
                
        except asyncio.CancelledError:
            print("ループが停止したのだ")
            self.kill_timer(user_id)
