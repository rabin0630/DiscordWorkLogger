from discord import interactions
import time
from datetime import datetime
import asyncio
import random
import datetime
from settings_env import env_mode

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import schemas

import logging
import time
from datetime import datetime

import discord
from discord import app_commands,Interaction
from discord.ext import commands

index = "" if env_mode == "prod" else "_test"

class Time_Stamp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(name=f"in{index}",description="出勤します")
  async def work_in(self,interaction:Interaction):
    user = interaction.user.mention
    
    user_id = interaction.user.id
    date_now = datetime.date.today()
    start_time_now = datetime.datetime.now()
        
    user_data: schemas.AttendanceCreate = schemas.AttendanceCreate(
        user_id = user_id,
        date = date_now,
        start_time = start_time_now
    )

    user_data_json: str = user_data.json()

    #TODO:aiohttpでapiに送信する。