import discord
import datetime
from datetime import date
from settings_env import env_mode,API_URL
from utils import random_choice_format_list_message
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend.schemas as schemas


from discord import app_commands
from discord.ext import commands
import requests

# TODO
## post文を書く
## api側でガード句（登録されたuser.id or nameがあるか）を書く

class Register(commands.Cog):
    # TODO: グローバルから引っ張ってるから良くない
    index = "" if env_mode == "prod" else "_test"
    
    REGISTER_COMPLETE_MESSAGES: list[str] = [
        "{name}の登録が完了したのだ！これからよろしくなのだ！",
        "ばっちり登録完了なのだ！{name}、一緒に頑張るのだ！",
        "登録できたのだ！{name}の働きぶり、楽しみにしてるのだ！",
        "{name}のデータをしっかり記録したのだ！任せるのだ！",
        "登録完了なのだ！{name}も今日からずんだもんの仲間なのだ！",
        "ようこそなのだ！{name}の登録を無事に受け付けたのだ！",
        "登録成功なのだ！{name}、気合入れていくのだー！",
        "{name}の登録がバッチリ終わったのだ！いつでも出勤するのだ！",
        "登録完了なのだ！{name}の活躍をボクが記録してあげるのだ！",
        "ピピピピ！{name}の登録が完了なのだ！よろしく頼むのだ！"
    ]
    
    REGISTER_ID_CONFLICT_MESSAGES: list[str] = [
        "お前のIDはすでに登録されているのだ！名前を変えたいなら更新機能を使うのだ！",
        "ん？お前はもう登録済みのはずなのだ！二重登録はできないのだ！",
        "すでにボクの仲間として登録されているのだ！出勤を待ってるのだ！",
        "おっと！このIDはすでに使われているのだ！更新機能でやり直すのだ！",
        "登録しようとしたけど、もうお前のデータはバッチリあるのだ！"
    ]
    
    REGISTER_NAME_CONFLICT_MESSAGES: list[str] = [
        "「{name}」という名前は他の人がすでに使っているのだ…別の名前にしてほしいのだ！",
        "残念だけど「{name}」は先約がいるのだ！少し変えてみてほしいのだ！",
        "「{name}」はもう使われているのだ！別の名前でリトライするのだ！",
        "ごめんなのだ！「{name}」は他の仲間が使っているみたいなのだ！",
        "「{name}」はすでに登録されている名前なのだ…！他のカッコいい名前を考えるのだ！"
    ]
    
    NO_DATA_AND_REGISTER_NAME_MESSAGES: list[str] = [
        "まだ名前が登録されていないのだ！先に名前を登録するのだ！",
        "おっと！お前のデータがまだないのだ。まずは登録からよろしくなのだ！",
        "だめなのだ！名前が登録されてないから確認できないのだ。先に登録コマンドを使うのだ！",
        "ボクの記録にお前の名前がないのだ！急いで登録するのだー！",
        "名無しの権兵衛はいやなのだ！先に名前の登録をお願いするのだ！"
    ]
    
    YOUR_NAME_MESSAGES: list[str] = [
        "お前の名前は「{name}」なのだ！",
        "ボクの記録によると、お前は「{name}」なのだ！間違いないのだ！",
        "お前の名前はズバリ！「{name}」なのだ！カッコいい名前なのだ！",
        "確認したのだ！お前は「{name}」としてバッチリ登録されているのだ！",
        "「{name}」！それがお前の名前なのだ！今日も一日頑張るのだ！"
    ]

    def __init__(self, bot):
        self.bot = bot
    
    # 名前を登録する
    @app_commands.command(name=f"register{index}", description="名前を登録します")
    async def register_command(self, interaction: discord.Interaction, name: str):
        """
        コマンドしたユーザーのuser_idを用いて、登録したuser_nameをdiscordに返す関数
        
        @param interaction: interactionの中にあるuser.id
        @return: discordに登録されたuser_name
        """
        if not name:
            await interaction.response.send_message("名前を書くのだ")
            return
        
        now: datetime.date = date.today()
        user_id: int = interaction.user.id
        
        member_data: schemas.Member = schemas.Member(
            user_id=user_id,
            user_name=name,
            created_date=now,
        )
        ### schemas.Memberに継承されたBasemodelのjsonメソッドを用いてjsonに変換する
        member_data_json: str = member_data.json()

        response: requests.Response = requests.post(f"{API_URL}/register_member", data=member_data_json)


        if response.status_code == 200:
            msg: str = random_choice_format_list_message(self.REGISTER_COMPLETE_MESSAGES, name=name)
            await interaction.response.send_message(msg)
            
        elif response.status_code == 409:
            # FastAPIから返ってきたエラーの詳細(detail)を取得するのだ
            error_detail = response.json().get("detail", "")
            
            if error_detail == "このIDはすでに使われています":
                msg: str = random_choice_format_list_message(self.REGISTER_ID_CONFLICT_MESSAGES, name=name)
                await interaction.response.send_message(msg)
            elif error_detail == "この名前はすでに使われています":
                msg: str = random_choice_format_list_message(self.REGISTER_NAME_CONFLICT_MESSAGES, name=name)
                await interaction.response.send_message(msg)
            else:
                await interaction.response.send_message("すでに登録されているみたいなのだ！")
        else:
            await interaction.response.send_message(f"登録に失敗したのだ… (ステータスコード: {response.status_code})")
    
    # 名前を返す
    @app_commands.command(name=f"myname{index}", description="名前を確認します")
    async def myname(self,interaction:discord.Interaction):
        """
        コマンドしたユーザーのuser_idを用いて、登録したuser_nameをdiscordに返す関数
        
        @param interaction: interactionの中にあるuser.id
        @return: discordに登録されたuser_name
        """
        user_id = interaction.user.id
        
        user_data: schemas.MemberIdOnly = schemas.MemberIdOnly(
            user_id = user_id
        )

        user_data_json: str = user_data.json()

        response: requests.Response = requests.post(f"{API_URL}/get_name", data=user_data_json)

        if response.status_code == 409:
            msg: str = random_choice_format_list_message(self.NO_DATA_AND_REGISTER_NAME_MESSAGES)
            await interaction.response.send_message(msg)
            
        elif response.status_code == 200:
            user_name = response.json()["user_name"]
            msg: str = random_choice_format_list_message(self.YOUR_NAME_MESSAGES, name=user_name)
            await interaction.response.send_message(msg)
            print(dir(response))

    
