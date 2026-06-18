import os
import asyncio
import aiohttp
import aiofiles
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from settings_env import env_mode
from google import genai

index = "" if env_mode == "prod" else "_test"

class Gemini_Zundamon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_active = False  # 初期状態はオフ

        if not os.path.exists("./wave"):
            os.makedirs("./wave")

    @app_commands.command(name=f"zundamon_connect{index}", description="Geminiずんだもん機能をオン/オフするのだ！")
    @app_commands.describe(password="パスワードを入力するのだ")
    async def toggle_gemini(self, interaction: Interaction, password: int):
        correct_password = os.getenv("ZUNDAMON_PASSWORD")
        
        # 環境変数にパスワードが設定されていない場合
        if not correct_password:
            await interaction.response.send_message(f"{correct_password}環境変数（.env）に `ZUNDAMON_PASSWORD` が設定されていないのだ！", ephemeral=True)
            return

        # パスワードチェック
        if str(password) != correct_password:
            await interaction.response.send_message("パスワードが違うのだ！出直してくるのだ！", ephemeral=True)
            return

        # 状態の切り替え
        self.is_active = not self.is_active
        status = "オン" if self.is_active else "オフ"
        await interaction.response.send_message(f"パスワード確認OKなのだ！Geminiずんだもん機能を **{status}** にしたのだ！")

    @app_commands.command(name=f"chat_zundamon{index}", description="ずんだもんとGeminiを使っておしゃべりするのだ！")
    @app_commands.describe(prompt="ずんだもんに聞きたいことを入力するのだ")
    async def chat_zunda(self, interaction: Interaction, prompt: str):
        # オフの場合は弾く
        if not self.is_active:
            await interaction.response.send_message("現在Geminiずんだもん機能はオフになっているのだ！`/zundamon_connect` でオンにしてほしいのだ！", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("まずはボイスチャンネルに入ってほしいのだ！", ephemeral=True)
            return

        await interaction.response.defer()

        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            await interaction.followup.send("GeminiのAPIキー（GEMINI_API_KEY）が設定されていないみたいなのだ！")
            return

        voicevox_key = os.getenv("VOICEVOX_KEY")
        if not voicevox_key:
            await interaction.followup.send("VoicevoxのAPIキー（VOICEVOX_KEY）が設定されていないみたいなのだ！")
            return

        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            voice_client = await interaction.user.voice.channel.connect()

        # 1. Gemini APIで回答を生成
        try:
            client = genai.Client(api_key=gemini_key)
            
            system_prompt = ""
            if os.path.exists("./gemini.md"):
                with open("./gemini.md", "r", encoding="utf-8") as f:
                    system_prompt = f.read()
            else:
                system_prompt = "君はずんだもんなのだ。語尾に『〜のだ』をつけて100文字以内で答えるのだ。"

            full_prompt = f"{system_prompt}\n\nユーザーからの質問: {prompt}"
            
            response = client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=full_prompt,
            )
            answer_text = response.text

        except Exception as e:
            await interaction.followup.send(f"Gemini APIのエラーなのだ…\n{e}")
            return

        # 2. Voicevox APIで音声を生成
        speaker_id = 3
        async with aiohttp.ClientSession() as session:
            url = f'https://api.su-shiki.com/v2/voicevox/audio/?key={voicevox_key}&speaker={speaker_id}&pitch=0&intonationScale=1&speed=1&text={answer_text}'
            async with session.post(url) as resp:
                if resp.status == 200:
                    r = await resp.read()
                    file_path = f"./wave/chat_zunda_{interaction.guild.id}.wav"
                    async with aiofiles.open(file_path, mode='wb') as f:
                        await f.write(r)
                else:
                    await interaction.followup.send("音声の作成に失敗しちゃったのだ…")
                    return

        while voice_client.is_playing():
            await asyncio.sleep(1)

        source = discord.FFmpegPCMAudio(file_path)
        trans = discord.PCMVolumeTransformer(source, volume=1.0)

        try:
            voice_client.play(trans)
            
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
            
            await interaction.followup.send(f"**質問:** {prompt}\n**ずんだもん:** {answer_text}")

        except discord.errors.ClientException:
            await interaction.followup.send("同時に音声は流せないのだ！")
