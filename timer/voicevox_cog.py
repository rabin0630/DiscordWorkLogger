import os
import asyncio
import aiohttp
import aiofiles
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from settings_env import env_mode

index = "" if env_mode == "prod" else "_test"

class Voicevox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists("./wave"):
            os.makedirs("./wave")

    @app_commands.command(name=f"connect_zundamon{index}", description="ずんだもんをボイスチャンネルに呼ぶのだ！")
    async def connect_zunda(self, interaction: Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("まずはキミがボイスチャンネルに入ってほしいのだ！", ephemeral=True)
            return
            
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            await interaction.user.voice.channel.connect()
            await interaction.response.send_message("ボイスチャンネルに接続したのだ！よろしくなのだ！")
        else:
            await interaction.response.send_message("もう既にボイスチャンネルにいるのだ！", ephemeral=True)

    @app_commands.command(name=f"disconnect_zundamon{index}", description="ずんだもんとおさらばなのだ")
    async def disconnect_zunda(self, interaction: Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message("ボイスチャンネルから切断したのだ！ばいばいなのだ！")
        else:
            await interaction.response.send_message("今はどこにも繋がっていないのだ！", ephemeral=True)

    @app_commands.command(name=f"zundamon{index}", description="ずんだもんがしゃべってくれるのだ！！")
    @app_commands.describe(text="しゃべらせる言葉")
    async def zunda(self, interaction: Interaction, text: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("まずはボイスチャンネルに入ってほしいのだ！", ephemeral=True)
            return

        # Discordの3秒ルール対策で、先に返信を済ませるのだ
        await interaction.response.send_message(f"ずんだもん「 {text} 」")

        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            voice_client = await interaction.user.voice.channel.connect()

        speaker_id = 3
        key = os.getenv("VOICEVOX_KEY") 
        if not key:
            await interaction.followup.send("APIキー（VOICEVOX_KEY）が設定されていないみたいなのだ！")
            return

        async with aiohttp.ClientSession() as session:
            url = f'https://api.su-shiki.com/v2/voicevox/audio/?key={key}&speaker={speaker_id}&pitch=0&intonationScale=1&speed=1&text={text}'
            async with session.post(url) as resp:
                if resp.status == 200:
                    r = await resp.read()
                    file_path = f"./wave/zunda_{interaction.guild.id}.wav"
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
        except discord.errors.ClientException:
            await interaction.followup.send("同時に音声は流せないのだ！")
