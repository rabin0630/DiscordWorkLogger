import re

with open("timer.py", "r") as f:
    content = f.read()

# 必要なモジュールの追加
if "import time" not in content:
    content = re.sub(r'import logging', "import logging\nimport time\nfrom datetime import datetime", content)

new_class = '''class Timer(commands.Cog):

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
        self.bot = bot
        self.activated_timer_data = {}  # タイマーをメモリで管理する簡易的なデータベース
        self.timer_tasks = {}

    # TODO: グローバルから引っ張ってるから良くない
    index = None if env_mode == "prod" else "_test"
    
    # タイマーを登録する
    async def register_timer(
        self, 
        user_id       : int, 
        is_active     : bool, 
        end_time      : float, 
        remaining_time_at_pause: float,
        is_pomodoro   : bool,
        minutes       : int,
        channel       : discord.abc.Messageable
    ):
        self.activated_timer_data[user_id] = {
            "is_active"     : is_active,
            "is_pomodoro"   : is_pomodoro,
            "end_time"      : end_time,
            "remaining_time_at_pause": remaining_time_at_pause,
            "minutes"       : minutes,
            "channel"       : channel
        }

    # メッセージ出力
    def random_choice_format_list_message(self, list_message: list[str], **kwargs):
        if not list_message:
            return print("メッセージが渡されませんでした")
        message = random.choice(list_message)
        message = message.format(**kwargs)
        return message

    def kill_timer(self, user_id: int):
        if not self.activated_timer_data.get(user_id):
            return print("タイマーが起動していません")
        self.activated_timer_data.pop(user_id, None)
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel()
        return

    # タイマーを開始する
    async def countdown(self, user_id: int, end_message: list = None):
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
                message = self.random_choice_format_list_message(end_message, mention=mention, minutes=minutes)
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
        front_time = self.log_delay(interaction, "timer_command")
        if minutes < 0:
            return

        user_id = interaction.user.id
        
        # 1.既にタイマーが起動しているかチェック
        user_timer = self.activated_timer_data.get(user_id)
        if user_timer:
            message = self.random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", minutes))
            await interaction.response.send_message(message)
            return

        try:
            # 2.timer_taskに情報を登録
            is_active = True
            end_time = front_time + (minutes * 60) # interaction.created_atを基準に計算
            remaining_time_at_pause = 0.0
            is_pomodoro = False
            await self.register_timer(user_id, is_active, end_time, remaining_time_at_pause, is_pomodoro, minutes, interaction.channel)
            
            # 3. discordにリアクションメッセージを送信
            message = self.random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=minutes)
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
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        message = self.random_choice_format_list_message(self.TIMER_STOP_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
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
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        if not user_timer["is_active"]:
            await interaction.response.send_message("すでに一時停止中なのだ！")
            return

        user_timer["is_active"] = False
        # フロントでボタンが押された時間基準で、残り時間を保存する
        user_timer["remaining_time_at_pause"] = user_timer["end_time"] - front_time
        
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel() # カウントダウンを一時停止
            
        message = self.random_choice_format_list_message(self.TIMER_PAUSE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
        await interaction.response.send_message(message)
        return

    # タイマーを表示する
    @app_commands.command(name=f"showtimer{index}", description="タイマーを表示します")
    async def timer_show(self, interaction: discord.Interaction):
        self.log_delay(interaction, "timer_show")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)
        
        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        # 残り時間を計算
        if user_timer["is_active"]:
            remaining_time = user_timer["end_time"] - time.time()
        else:
            remaining_time = user_timer["remaining_time_at_pause"]

        if remaining_time < 0:
            remaining_time = 0

        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)

        message = self.random_choice_format_list_message(self.TIMER_REMAINING_MESSAGES, mention=interaction.user.mention, minutes=minutes, seconds=seconds)
        await interaction.response.send_message(message)

    # タイマーを再開する
    @app_commands.command(name=f"resume_timer{index}", description="タイマーを再開します")
    async def timer_resume(self, interaction: discord.Interaction):
        front_time = self.log_delay(interaction, "timer_resume")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)

        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        if user_timer["is_active"] == True:
            await interaction.response.send_message("起動中だよ")
            return

        try:
            user_timer["is_active"] = True
            # 新しい終了時刻を計算
            user_timer["end_time"] = front_time + user_timer["remaining_time_at_pause"]
            user_timer["remaining_time_at_pause"] = 0.0

            message = self.random_choice_format_list_message(self.TIMER_RESUME_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            
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
        front_time = self.log_delay(interaction, "timer_pomodoro")
        user_id = interaction.user.id
        user_timer = self.activated_timer_data.get(user_id)
        if user_timer:
            message = self.random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer.get("minutes", 0))
            await interaction.response.send_message(message)
            return

        try:
            is_active = True
            end_time = front_time + (25 * 60)
            is_pomodoro = True
            await self.register_timer(
                user_id, is_active, end_time, 0.0, is_pomodoro, 25, interaction.channel
            )

            message = self.random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=25)
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
'''

pattern = r'class Timer\(commands\.Cog\):.*?(?=@bot\.event)'
new_content = re.sub(pattern, new_class, content, flags=re.DOTALL)

with open("timer.py", "w") as f:
    f.write(new_content)

