import datetime
import gspread
import json


sheet_id = USER_SHEET_MAPPING.get(user_id)

    # # スプレッドシートID が見つからない場合はスキップ
    # if not sheet_id:
    #     print(f"ユーザー ID {user_id} に対応するスプレッドシートIDが見つかりません。")
    #     await message.add_reaction("❓")
    #     return

    # if gc is None:
    #     print(
    #         "service_account.json が正しく読み込めていません。設定を確認してください。"
    #     )
    #     await message.add_reaction("⚠️")
    #     return

# ユーザー ID と スプレッドシートID のマッピングをロード
with open("user_sheet_mapping.json", "r") as f:
    USER_SHEET_MAPPING = json.load(f)

# gspread のクライアントを準備
gc = None
try:
    gc = gspread.service_account(filename="service_account.json")
except Exception as e:
    print(f"service_account.jsonの読み込みに失敗しました: {e}")

def get_current_sheet(spreadsheet):
    """現在の集計シートを選ぶ"""
    today = datetime.now()
    year_str = str(today.year)[-2:]  # '24'
    month = today.month
    day = today.day

    # 16日以降なら翌月、1日～15日なら今月シートを参照
    target_month = month + 1 if day > 15 else month

    sheet_name = f"{year_str}年{target_month}月"
    return spreadsheet.worksheet(sheet_name)


def get_or_create_today_row(sheet):
    """B列から今日の日付の行を見つける。なければ末尾に作成する。"""
    b_col = sheet.col_values(2)
    today = datetime.now()

    # スプレッドシート上の表記ブレを考慮したパターンの作成
    today_patterns = [
        f"{today.month}/{today.day}",
        f"{today.month:02d}/{today.day:02d}",
        today.strftime("%Y/%m/%d"),
        today.strftime("%Y/%-m/%-d"),
    ]

    for idx, val in enumerate(b_col):
        if not val:
            continue
        for pat in today_patterns:
            if pat in val:
                return idx + 1

    # 見つからなかった場合は末尾に新しい行を作成
    all_records = sheet.get_all_values()
    new_row_idx = len(all_records) + 1

    # B列(2)に今日の日付を書き込む
    new_date_str = f"{today.month}/{today.day}"
    sheet.update_cell(new_row_idx, 2, new_date_str)

    return new_row_idx


def record_checkin(spreadsheet, mode):
    sheet = get_current_sheet(spreadsheet)
    row = get_or_create_today_row(sheet)

    time_str = datetime.now().strftime("%H:%M")
    # D列(4)に mode、E列(5)に時刻
    sheet.update_cell(row, 4, mode)
    sheet.update_cell(row, 5, time_str)


def record_checkout(spreadsheet):
    sheet = get_current_sheet(spreadsheet)
    row = get_or_create_today_row(sheet)

    time_str = datetime.now().strftime("%H:%M")
    # F列(6)に退勤時刻、G列(7)に休憩時間
    sheet.update_cell(row, 6, time_str)
    sheet.update_cell(row, 7, "1:00")