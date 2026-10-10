"""utils.py(表示の部品)の単体テスト"""
from datetime import datetime

import pytest

from utils import format_minutes, format_start_time, format_time


# U-06
@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2026, 10, 8, 9, 30), "9:30"),
        (datetime(2026, 10, 8, 18, 0), "18:00"),
        (datetime(2026, 10, 9, 0, 0), "0:00"),
        (datetime(2026, 10, 8, 9, 5), "9:05"),
    ],
)
def test_format_time(dt: datetime, expected: str):
    # 時刻を「時:分」にする。時は0埋めせず、分は2桁にする
    assert format_time(dt) == expected


# U-10
@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (510, "8:30"),
        (0, "0:00"),
        (30, "0:30"),
        (900, "15:00"),
        (1800, "30:00"),
    ],
)
def test_format_minutes(minutes: int, expected: str):
    # 分数を「時間:分」にする。24時間を超えてもそのまま時間で表す
    assert format_minutes(minutes) == expected


# U-17
@pytest.mark.parametrize(
    ("start", "now", "expected"),
    [
        (datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 12, 40), "9:30"),
        (datetime(2026, 10, 7, 21, 30), datetime(2026, 10, 8, 12, 40), "前日21:30"),
        (datetime(2026, 10, 1, 21, 30), datetime(2026, 10, 8, 12, 40), "10/1 21:30"),
        (datetime(2026, 10, 9, 0, 0), datetime(2026, 10, 8, 23, 50), "翌0:00"),
        (datetime(2026, 9, 30, 21, 30), datetime(2026, 10, 1, 9, 0), "前日21:30"),
        (datetime(2025, 12, 31, 21, 30), datetime(2026, 1, 1, 9, 0), "前日21:30"),
    ],
)
def test_format_start_time(start: datetime, now: datetime, expected: str):
    # 出勤時刻に、nowの日付から見た日付を付ける。月や年をまたいでも「前日」になる
    assert format_start_time(start, now) == expected
