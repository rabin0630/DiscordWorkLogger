import time
import datetime
from datetime import date
import asyncio
from settings_env import env_mode

import discord
from discord import app_commands
from discord.ext import commands

# TODO
## post文を書く
## api側でガード句（登録されたuser.id or nameがあるか）を書く

class Register(commands.Cog):
  # TODO: グローバルから引っ張ってるから良くない
  index = "" if env_mode == "prod" else "_test"
  
  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(name=f"register{index}", description="名前を登録します")
  async def register_command(self, interaction: discord.Interaction, name: str):
    if not name:
      return interaction.response.send_message("名前を書くのだ")
    
    now = date.today()
    user_id = interaction.user.id

    await interaction.response.send_message(f"{now}:{user_id}:{name}")
    

    
