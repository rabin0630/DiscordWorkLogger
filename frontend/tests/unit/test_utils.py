"""utils.py(表示の部品)の単体テスト"""
from datetime import datetime

import pytest

from utils import format_minutes, format_time


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
