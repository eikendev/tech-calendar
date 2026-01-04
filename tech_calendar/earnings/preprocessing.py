"""
Preprocessing helpers for earnings events.
"""

from collections.abc import Iterable

from tech_calendar.earnings.models import EarningsEvent


def filter_events(events: Iterable[EarningsEvent], allowed: Iterable[str] | None) -> list[EarningsEvent]:
    """
    Return earnings events whose ticker is in `allowed`, ensuring uniqueness
    per (ticker, fiscal year, quarter). Normalizes tickers to uppercase and strips whitespace.
    """
    if allowed:
        allowed_set = {s.strip().upper() for s in allowed if s and s.strip()}
        filtered = {
            (ev.ticker.upper(), ev.event_year(), ev.quarter): ev for ev in events if ev.ticker.upper() in allowed_set
        }
        return list(filtered.values())

    filtered = {(ev.ticker.upper(), ev.event_year(), ev.quarter): ev for ev in events}
    return list(filtered.values())
