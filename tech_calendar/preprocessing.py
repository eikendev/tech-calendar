from collections.abc import Iterable

from .models import EarningsEvent


def filter_events(events: Iterable[EarningsEvent], allowed: Iterable[str] | None) -> list[EarningsEvent]:
    """
    Return earnings events whose ticker is in `allowed`, ensuring uniqueness
    per (ticker, quarter). Normalizes tickers to uppercase and strips whitespace.
    """
    if allowed:
        allowed_set = {s.strip().upper() for s in allowed if s and s.strip()}
        return list({(ev.ticker, ev.quarter): ev for ev in events if ev.ticker.upper() in allowed_set}.values())
    else:
        return list({(ev.ticker, ev.quarter): ev for ev in events}.values())
