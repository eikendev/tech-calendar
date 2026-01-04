"""
Earnings calendar orchestration.
"""

from datetime import date, timedelta
from pathlib import Path

from tech_calendar.calendar import CalendarMetadata, build_and_write_calendar, make_all_day_event
from tech_calendar.config import AppConfig, EarningsConfig
from tech_calendar.constants import ENV_FINNHUB_API_KEY
from tech_calendar.earnings.finnhub_client import fetch_finnhub_earnings
from tech_calendar.earnings.preprocessing import filter_events
from tech_calendar.logging import get_logger
from tech_calendar.storage import Database, EarningsRepository

logger = get_logger(__name__)


def run_earnings(config: AppConfig, *, today: date | None = None) -> Path:
    """
    Generate the earnings ICS file using Finnhub data and persisted storage.
    """
    db_path = config.storage.db_path
    api_key = _resolve_finnhub_api_key(config.earnings)

    if not config.earnings.tickers:
        logger.error("no_tickers_configured")
        raise SystemExit(2)

    reference_date = today or date.today()
    start = reference_date - timedelta(days=config.earnings.days_past)
    end = reference_date + timedelta(days=config.earnings.days_ahead)

    logger.info(
        "fetch_start",
        extra={
            "api": "finnhub",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "tickers": ",".join(config.earnings.tickers),
        },
    )

    events = fetch_finnhub_earnings(start, end, api_key)
    selected_events = filter_events(events, config.earnings.tickers)

    with Database(db_path) as db:
        earnings_repo = EarningsRepository(db.connection)
        earnings_repo.save_events(selected_events)
        calendar_events = earnings_repo.list_for_calendar(
            current_year=reference_date.year,
            retention_years=config.earnings.calendar.retention_years,
        )

    metadata = CalendarMetadata(
        name=config.earnings.calendar.name,
        relcalid=config.earnings.calendar.relcalid,
        description=config.earnings.calendar.description,
    )
    out_path = build_and_write_calendar(
        calendar_events,
        metadata,
        lambda ev, relcalid: make_all_day_event(
            ev.date,
            uid=ev.uid(relcalid),
            name=ev.name(),
            description=ev.description(),
        ),
        config.earnings.calendar.ics_path,
    )

    logger.info(
        "earnings_ics_written",
        extra={
            "path": str(out_path),
            "events_total": len(calendar_events),
            "fetched_total": len(selected_events),
        },
    )
    return Path(out_path)


def _resolve_finnhub_api_key(config: EarningsConfig) -> str:
    """
    Read the Finnhub API key from config or the environment.
    """
    from os import getenv

    api_key = config.api_key or getenv(ENV_FINNHUB_API_KEY)
    if not api_key:
        logger.error("api_key_missing")
        raise SystemExit(2)
    return api_key
