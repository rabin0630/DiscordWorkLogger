"""/helpのCogの単体テスト"""
from cogs.help_cog import Help


# U-01
def test_help_message():
    # ヘルプメッセージの内容が正しいことを確認する
    expected = (
        "【従業員専用】\n"
        "/register {name} … 名前を登録する\n"
        "/myname … 登録した名前を確認する\n"
        "/rename {name} … 登録した名前を変更する\n"
        "/start_work … 出勤を記録する\n"
        "/stop_work … 退勤を記録する\n"
        "/work_status … 自分の出勤状況を確認する\n"
        "【社長専用】\n"
        "/all_work_status … 社長以外の全員の出勤状況を確認する\n"
        "【全員】\n"
        "/help … コマンドの説明を表示する"
    )
    assert Help.HELP_MESSAGE == expected
