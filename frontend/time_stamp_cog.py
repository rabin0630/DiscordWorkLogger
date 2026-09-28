from settings_env import API_URL
from utils import random_choice_format_list_message
import datetime
import json
from settings_env import env_mode
import requests

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
        
    # APIに送るデータ。日付と時刻はJSONで送れるように文字列にする
    user_data: dict = {
        "user_id": user_id,
        "date": str(date_now),
        "start_time": start_time_now.isoformat(),
    }
    user_data_json: str = json.dumps(user_data)

    response: requests.Response = requests.post(f"{API_URL}/start_work", data=user_data_json, headers={"Content-Type": "application/json"})

    # TODO データベースにあるuser_nameを用いてmsgをformatする
    if response.status_code == 200:
        msg: str = random_choice_format_list_message(self.REGISTER_COMPLETE_MESSAGES, name=name)
        await interaction.response.send_message(msg)