"""
Tests for calendar all-day helper functions.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from tech_calendar.calendar import _all_day_begin_local, _all_day_bounds
from tech_calendar.constants import EXCHANGE_TZ


def test_all_day_begin_local_uses_exchange_timezone():
    target = date(2025, 5, 2)

    result = _all_day_begin_local(target)

    assert result.date() == target
    assert result.hour == 0 and result.minute == 0 and result.second == 0
    assert result.tzinfo == ZoneInfo(EXCHANGE_TZ)


def test_all_day_bounds_spans_full_days_inclusively():
    start = date(2025, 5, 2)
    end = date(2025, 5, 5)

    begin_dt, end_dt = _all_day_bounds(start, end)

    assert begin_dt == datetime(2025, 5, 2, 0, 0)
    assert end_dt == datetime(2025, 5, 6, 0, 0)
    assert begin_dt.tzinfo is None and end_dt.tzinfo is None
