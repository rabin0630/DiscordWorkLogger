from aiohttp import request
import discord
import time
import datetime
from datetime import date
import asyncio
from settings_env import env_mode,API_URL


import discord
from discord import app_commands
from discord.ext import commands

import requests

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

    data = {
        "user_id": user_id,
        "user_name": name,
        "created_date": str(now),
        "retirement_date": None
    }
    response = requests.post(f"{API_URL}/register_member", json=data)

    await interaction.response.send_message(response.status_code)
  
  # 名前を返す
  @app_commands.command(name=f"myname{index}", description="名前を確認します")
  async def myname(self,interaction:discord.Interaction):
      data = {"user_id":interaction.user.id}

      response = requests.post(f"{API_URL}/get_name", json=data)

      if response.status_code == 409:
          await interaction.response.send_message("まだ名前が登録されていないのだ！先に名前を登録するのだ！")
      elif response.status_code == 200:
          user_name = response.json()["user_name"]
          await interaction.response.send_message(f"お前の名前は「{user_name}」なのだ！")

    
