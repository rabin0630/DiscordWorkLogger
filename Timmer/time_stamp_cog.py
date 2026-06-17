from discord import interactions
import time
from datetime import datetime
import asyncio
import random
import datetime
from settings_env import env_mode


import logging
import time
from datetime import datetime

import discord
from discord import app_commands,Interaction
from discord.ext import commands

index = None if env_mode == "prod" else "_test"

class Time_Stamp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(name=f"in{index}",description="出勤します")
  async def work_in(self,interaction:Interaction):
    user_id = interaction.user.mention
    
    await interaction.response.send_message(f"{user_id} 出勤を記録したのだ！")