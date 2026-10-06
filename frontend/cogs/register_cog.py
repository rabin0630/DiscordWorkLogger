import json

import discord
import requests
from discord import app_commands
from discord.ext import commands

from services import api_client
from services.api_client import ApiResponse
from settings_env import env_mode, API_URL
from utils import random_choice_format_list_message, EMPLOYEE_ONLY_MESSAGES, API_UNAVAILABLE_MESSAGES


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
    
    # 名前のルールのメッセージ。/renameでも使う
    NAME_EMPTY_MESSAGES: list[str] = [
        "名前を書くのだ！",
        "名前が空っぽなのだ！ちゃんと書いてほしいのだ！",
        "名前を入れ忘れているのだ！もう一度書くのだ！",
    ]

    NAME_NOT_ALPHA_MESSAGES: list[str] = [
        "英字以外は書けないのだ！",
        "名前は英字(A〜Z、a〜z)だけで書いてほしいのだ！",
        "ひらがなや数字、記号、空白は使えないのだ！英字だけにするのだ！",
    ]

    NAME_TOO_LONG_MESSAGES: list[str] = [
        "名前は10文字までなのだ！",
        "名前が長すぎるのだ！10文字までにしてほしいのだ！",
        "10文字を超えているのだ！もう少し短くするのだ！",
    ]

    ALREADY_REGISTERED_MESSAGES: list[str] = [
        "もう登録されているのだ！名前を変えたい時は/renameを使うのだ！",
        "ん？お前はもう登録済みなのだ！名前を変えたいなら/renameを使うのだ！",
        "すでにボクの仲間として登録されているのだ！名前を変える時は/renameなのだ！",
    ]

    NAME_TAKEN_MESSAGES: list[str] = [
        "「{name}」は他の人が使っているのだ…別の名前にしてほしいのだ！",
        "残念だけど「{name}」は先約がいるのだ！少し変えてみてほしいのだ！",
        "ごめんなのだ！「{name}」は他の仲間が使っているみたいなのだ！",
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
    @app_commands.describe(name="英字のみ、10文字まで")
    @app_commands.guild_only()
    async def register_command(self, interaction: discord.Interaction, name: str) -> None:
        """名前を登録し、結果をサーバーの全員に見える形で返信する

        Args:
            interaction (discord.Interaction): コマンドのinteraction。interaction.user.idを登録に使う
            name (str): 登録する名前。ルールの確認はAPIで行うので、そのまま送る
        """
        await interaction.response.defer()
        payload = {"user_id": interaction.user.id, "user_name": name}
        try:
            response = await api_client.post("/register_member", payload)
        except api_client.ApiUnavailableError:
            await interaction.followup.send(random_choice_format_list_message(API_UNAVAILABLE_MESSAGES))
            return
        await interaction.followup.send(make_register_reply(response, name))

    # 名前を返す
    @app_commands.command(name=f"myname{index}", description="名前を確認します")
    async def myname(self,interaction:discord.Interaction):
        """
        コマンドしたユーザーのuser_idを用いて、登録したuser_nameをdiscordに返す関数
        
        @param interaction: interactionの中にあるuser.id
        @return: discordに登録されたuser_name
        """
        user_id = interaction.user.id
        
        user_data: dict = {"user_id": user_id}
        user_data_json: str = json.dumps(user_data)

        response: requests.Response = requests.post(f"{API_URL}/get_name", data=user_data_json, headers={"Content-Type": "application/json"})

        if response.status_code == 409:
            msg: str = random_choice_format_list_message(self.NO_DATA_AND_REGISTER_NAME_MESSAGES)
            await interaction.response.send_message(msg)
            
        elif response.status_code == 200:
            user_name = response.json()["user_name"]
            msg: str = random_choice_format_list_message(self.YOUR_NAME_MESSAGES, name=user_name)
            await interaction.response.send_message(msg)
            print(dir(response))


# /register_memberのdetailと、返すメッセージのリスト
REGISTER_ERROR_MESSAGES: dict[str, list[str]] = {
    "employee_only": EMPLOYEE_ONLY_MESSAGES,
    "name_empty": Register.NAME_EMPTY_MESSAGES,
    "name_not_alpha": Register.NAME_NOT_ALPHA_MESSAGES,
    "name_too_long": Register.NAME_TOO_LONG_MESSAGES,
    "already_registered": Register.ALREADY_REGISTERED_MESSAGES,
    "name_taken": Register.NAME_TAKEN_MESSAGES,
}


def make_register_reply(response: ApiResponse, name: str) -> str:
    """/register_memberの結果から、返信の文を作る

    Discordを使わないので、単体テストできる。

    Args:
        response (ApiResponse): /register_memberの結果
        name (str): 従業員が入力した名前。name_takenのメッセージに入れる

    Returns:
        str: ランダムに選んだ返信の文。表にないdetailの時は、通信できなかった時の文
    """
    if response.status == 200:
        return random_choice_format_list_message(
            Register.REGISTER_COMPLETE_MESSAGES, name=response.body["user_name"])
    detail = response.body.get("detail")
    # 422の時はdetailがリストで返ってくるので、文字列の時だけ探す
    messages = REGISTER_ERROR_MESSAGES.get(detail) if isinstance(detail, str) else None
    if messages is None:
        return random_choice_format_list_message(API_UNAVAILABLE_MESSAGES)
    return random_choice_format_list_message(messages, name=name)
