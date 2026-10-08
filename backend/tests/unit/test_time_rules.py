"""time_rules(30分単位の丸めと、時間の計算)の単体テスト"""
from datetime import datetime, timedelta, timezone

import pytest

from src.services.time_rules import ceil_30, floor_30, minutes_between, to_jst


# U-02
@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2026, 10, 8, 9, 0), datetime(2026, 10, 8, 9, 0)),
        (datetime(2026, 10, 8, 9, 1), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 9, 29), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 9, 30, 59), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 23, 45), datetime(2026, 10, 9, 0, 0)),
    ],
)
def test_ceil_30(dt: datetime, expected: datetime):
    # 秒を切り捨ててから、30分単位で切り上げる。23:45は翌日の0:00になる
    assert ceil_30(dt) == expected


# U-03
@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2026, 10, 8, 9, 0), datetime(2026, 10, 8, 9, 0)),
        (datetime(2026, 10, 8, 9, 1), datetime(2026, 10, 8, 9, 0)),
        (datetime(2026, 10, 8, 9, 29), datetime(2026, 10, 8, 9, 0)),
        (datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 9, 59, 59), datetime(2026, 10, 8, 9, 30)),
        (datetime(2026, 10, 8, 23, 45), datetime(2026, 10, 8, 23, 30)),
    ],
)
def test_floor_30(dt: datetime, expected: datetime):
    # 秒を切り捨ててから、30分単位で切り捨てる
    assert floor_30(dt) == expected


# U-04
@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 14, 30), 300),
        (datetime(2026, 10, 8, 9, 30), datetime(2026, 10, 8, 9, 0), 0),
    ],
)
def test_minutes_between(start: datetime, end: datetime, expected: int):
    # startからendまでの分数。マイナスにはならない
    assert minutes_between(start, end) == expected


# U-05
def test_to_jst():
    # UTCの時刻が、タイムゾーンなしの日本時間になり、秒より細かい値はなくなる
    utc = datetime(2026, 10, 8, 0, 5, 12, 789000, tzinfo=timezone.utc)

    assert to_jst(utc) == datetime(2026, 10, 8, 9, 5, 12)
    assert to_jst(utc).tzinfo is None
    # 日本時間で来た時も同じ結果になる
    assert to_jst(utc.astimezone(timezone(timedelta(hours=9)))) == datetime(2026, 10, 8, 9, 5, 12)
