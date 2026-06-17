import logging
from discord import app_commands
import asyncio
import os
import discord
import random
from dotenv import load_dotenv
from discord.ext import commands

# envファイル取得
load_dotenv()

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_timer_bot.log", encoding="utf-8"), # テスト用に名前変更
        logging.StreamHandler()
    ]
)

env_mode = os.getenv("ENV")
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))

ACTIVITY = discord.Game("タイマー(Cog版)" if env_mode == "prod" else "test")

intents = discord.Intents.default()
intents.message_content = True

# ClientからBotに変更
bot = commands.Bot(
    command_prefix="!", # プレフィックス型コマンド用（helloコマンド等）
    status=discord.Status.online,
    intents=intents,
    activity=ACTIVITY
)

index = None if env_mode == "prod" else "_test"

class TimerCog(commands.Cog):
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
        "{mention} タイマーを再開するのだ！",
        "{mention} 作業再開なのだ！",
        "{mention} 頑張るのだ！",
    ]

    def __init__(self, bot):
        self.bot = bot
        # インスタンス変数として管理
        # {user_id: {"is_active": bool, "remaining_time": int, "is_pomodoro": bool, "minutes": int, "channel": discord.abc.Messageable}}
        self.activated_timer_datas = {}
        # 非同期タスクの参照を保持する辞書
        self.timer_tasks = {}

    def random_choice_format_list_message(self, list_message: list[str], **kwargs):
        if not list_message:
            return "メッセージが渡されませんでした"

        message = random.choice(list_message)
        message = message.format(**kwargs)
        return message

    def kill_timer(self, user_id: int):
        self.activated_timer_datas.pop(user_id, None)
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel()

    async def update_remaining_time(self, user_id: int, remaining_time: int):
        user_timer = self.activated_timer_datas.get(user_id)
        if not user_timer:
            return
        user_timer["remaining_time"] = remaining_time

    async def countdown(self, user_id: int, end_message: list):
        user_timer = self.activated_timer_datas.get(user_id)
        if not user_timer:
            return
        
        channel = user_timer["channel"]
        minutes = user_timer["minutes"]
        mention = f"<@{user_id}>"

        try:
            while user_timer["remaining_time"] > 0 and user_timer.get("is_active"):
                await asyncio.sleep(1)
                user_timer["remaining_time"] -= 1

            if user_timer["remaining_time"] <= 0:
                message = self.random_choice_format_list_message(end_message, mention=mention, minutes=minutes)
                await channel.send(message)
                self.kill_timer(user_id)
                
        except asyncio.CancelledError:
            print(f"ユーザー {user_id} のカウントダウンが一時停止またはキャンセルされたのだ")

    @app_commands.command(name=f"timer{index}", description="指定された時間のタイマーをセットします")
    async def timer_command(self, interaction: discord.Interaction, minutes: int):
        logging.info("timerコマンドを使用しました。")
        if minutes < 0:
            return await interaction.response.send_message("0以上の数値を指定するのだ！", ephemeral=True)
            
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if user_timer:
            message = self.random_choice_format_list_message(
                self.TIMER_ALREADY_ACTIVE_MESSAGES, 
                mention=interaction.user.mention, 
                minutes=user_timer["minutes"]
            )
            await interaction.response.send_message(message)
            return

        self.activated_timer_datas[user_id] = {
            "is_active": True,
            "remaining_time": minutes * 60,
            "is_pomodoro": False,
            "minutes": minutes,
            "channel": interaction.channel
        }

        message = self.random_choice_format_list_message(self.TIMER_SET_MESSAGES, mention=interaction.user.mention, minutes=minutes)
        await interaction.response.send_message(message)

        task = asyncio.create_task(self.countdown(user_id, self.TIMER_END_MESSAGES))
        self.timer_tasks[user_id] = task

    @app_commands.command(name=f"showtimer{index}", description="タイマーを表示します")
    async def timer_show(self, interaction: discord.Interaction):
        logging.info("showコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        remaining_time = user_timer["remaining_time"]
        mins = remaining_time // 60
        secs = remaining_time % 60

        message = self.random_choice_format_list_message(
            self.TIMER_REMAINING_MESSAGES, 
            mention=interaction.user.mention, 
            minutes=mins, 
            seconds=secs
        )
        await interaction.response.send_message(message)

    @app_commands.command(name=f"stoptimer{index}", description="タイマーを停止します")
    async def timer_stop(self, interaction: discord.Interaction):
        logging.info("stopコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        message = self.random_choice_format_list_message(self.TIMER_STOP_MESSAGES, mention=interaction.user.mention, minutes=user_timer["minutes"])
        await interaction.response.send_message(message)
        self.kill_timer(user_id)

    @app_commands.command(name=f"pausetimer{index}", description="タイマーを一時停止します")
    async def timer_pause(self, interaction: discord.Interaction):
        logging.info("pauseコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        user_timer["is_active"] = False
        task = self.timer_tasks.pop(user_id, None)
        if task:
            task.cancel() # カウントダウンを一時停止
            
        message = self.random_choice_format_list_message(self.TIMER_PAUSE_MESSAGES, mention=interaction.user.mention, minutes=user_timer["minutes"])
        await interaction.response.send_message(message)

    @app_commands.command(name=f"resume_timer{index}", description="タイマーを再開します")
    async def timer_resume(self, interaction: discord.Interaction):
        logging.info("resumeコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if not user_timer:
            message = self.random_choice_format_list_message(self.TIMER_NOT_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=0)
            await interaction.response.send_message(message)
            return

        user_timer["is_active"] = True
        message = self.random_choice_format_list_message(self.TIMER_RESUME_MESSAGES, mention=interaction.user.mention, minutes=user_timer["minutes"])
        await interaction.response.send_message(message)
        
        # カウントダウンタスクを再開
        task = asyncio.create_task(self.countdown(user_id, self.TIMER_END_MESSAGES))
        self.timer_tasks[user_id] = task

    @app_commands.command(name=f"pomodorotimer{index}", description="ポモドーロタイマーをセットします")
    async def timer_pomodoro(self, interaction: discord.Interaction, sets: int = 4):
        logging.info("pomodoroコマンドを使用しました。")
        user_id = interaction.user.id
        user_timer = self.activated_timer_datas.get(user_id)
        
        if user_timer:
            message = self.random_choice_format_list_message(self.TIMER_ALREADY_ACTIVE_MESSAGES, mention=interaction.user.mention, minutes=user_timer["minutes"])
            await interaction.response.send_message(message)
            return

        await interaction.response.send_message("ポモドーロ機能は現在準備中なのだ！（TODO）", ephemeral=True)





# ボイスチャンネルの入退室を通知（最小限構成）
class vc_count(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name='on_voice_state_update')
    async def voice_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        # Botの入退室は無視するのだ
        if member.bot:
            return

        # 送信先のチャンネル（システムのデフォルトチャンネル等）を取得
        channel = member.guild.system_channel
        if channel is None:
            return

        # ボイスチャンネルを移動したかどうか
        check = before.channel and after.channel and before.channel != after.channel

        # 退出した場合
        if after.channel is None or check:
            await channel.send(f"現在{len(before.channel.members)}人 <@{member.id}>が {before.channel.name} から退出したのだ！")

        # 入室の場合
        if before.channel is None or check:
            await channel.send(f"現在{len(after.channel.members)}人 <@{member.id}>が {after.channel.name} に参加したのだ！")

@bot.event
async def on_ready():
    logging.info(f"Timer Bot Logged in as {bot.user}!")
    logging.info("起動しました!")
    
    await bot.add_cog(TimerCog(bot))
    
    
    # プレフィックスコマンドではなく、スラッシュコマンドをDiscordに同期させる
    bot.tree.copy_global_to(guild=discord.Object(id=TARGET_GUILD_ID))
    await bot.tree.sync(guild=discord.Object(id=TARGET_GUILD_ID))

if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("DISCORD_TOKEN が .env ファイルに設定されていません。")
