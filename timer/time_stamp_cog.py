from settings_env import API_URL
from utils import random_choice_format_list_message
from discord import interactions
import time
from datetime import datetime
import datetime
from settings_env import env_mode
import requests

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

  @app_commands.command(name=f"start_work{index}",description="出勤します")
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

    response: requests.Response = requests.post(f"{API_URL}/start_work", data=user_data_json)

    # TODO データベースにあるuser_nameを用いてmsgをformatする
    if response.status_code == 200:
        msg: str = random_choice_format_list_message(self.REGISTER_COMPLETE_MESSAGES, name=name)
        await interaction.response.send_message(msg)