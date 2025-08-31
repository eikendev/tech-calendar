from datetime import date

import pytest

from tech_calendar.models import EarningsEvent
from tech_calendar.preprocessing import filter_events


@pytest.mark.parametrize(
    "allowed,events,expected_keys",
    [
        pytest.param(
            ["  aapl ", "MSFT", "", "   "],
            [
                EarningsEvent("AAPL", date(2025, 1, 30), 1),
                EarningsEvent("AAPL", date(2025, 1, 31), 1),
                EarningsEvent("MSFT", date(2025, 2, 15), 2),
                EarningsEvent("TSLA", date(2025, 3, 15), 1),
            ],
            {("AAPL", 1), ("MSFT", 2)},
            id="basic-case-normalization-and-dedupe",
        ),
        pytest.param(
            ["msft"],
            [
                EarningsEvent("MSFT", date(2024, 11, 5), 4),
                EarningsEvent("MSFT", date(2024, 11, 6), 4),
            ],
            {("MSFT", 4)},
            id="single-allowed",
        ),
    ],
)
def test_filter_events_filters_and_deduplicates(allowed, events, expected_keys):
    result = filter_events(events, allowed)
    by_key = {(ev.ticker, ev.quarter): ev for ev in result}
    assert set(by_key.keys()) == expected_keys
