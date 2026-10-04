import os
import discord


from dotenv import load_dotenv
from timer import Timer
from time_stamp_cog import Time_Stamp
from register_cog import Register
from help_cog import Help
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
## ファイルの分割をする;;;

# FIXME

# HACK

# XXX
## pomodoro_timer : 不明


# TEST環境の時は引数TEST_TOKENとTEST_CHANNEL_IDに変更
# (HACK)リファクタリングした方がいい。とてもみにくい


# envファイル取得
load_dotenv()

# 初期設定
env_mode = os.getenv("ENV")
print(env_mode)
env = "TARGET" if env_mode == "prod" else "TEST"

DISCORD_TOKEN: str = os.getenv(f"{env}_TOKEN")
TARGET_GUILD_ID = int(os.getenv(f"{env}_GUILD_ID"))
ACTIVITY = discord.Game("タイマー" if env_mode == "prod" else "test")  # botのステータス

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!", # プレフィックス型コマンド用（helloコマンド等）
    status=discord.Status.online,
    intents=intents,
    activity=ACTIVITY
)

@bot.event
async def on_ready():
    # 起動時
    print(f"Logged in as {bot.user}!")
    await bot.add_cog(Timer(bot))
    await bot.add_cog(Time_Stamp(bot))
    await bot.add_cog(Register(bot))
    await bot.add_cog(Help(bot))

    # グローバルコマンドを特定のサーバーにコピーして即時反映させるのだ！
    target_guild = discord.Object(id=TARGET_GUILD_ID)
    bot.tree.copy_global_to(guild=target_guild)
    await bot.tree.sync(guild=target_guild)
    print("コマンドの即時反映が完了したのだ！")



# ボットを起動
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN が .env ファイルに設定されていません。")
