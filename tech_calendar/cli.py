from datetime import date, timedelta

from .calendar import build_calendar
from .file_utils import write_text_file
from .finnhub_client import fetch_finnhub_earnings
from .logging import configure_logging, get_logger
from .preprocessing import filter_events
from .settings import Settings

logger = get_logger(__name__)


def _run() -> None:
    settings = Settings.from_env()

    if not settings.tickers:
        logger.error("no_tickers_configured")
        raise SystemExit(2)

    if not settings.api_key:
        logger.error("api_key_missing")
        raise SystemExit(2)

    today = date.today()
    start = today - timedelta(days=settings.days_past)
    end = today + timedelta(days=settings.days_ahead)

    logger.info(
        "fetch_start",
        extra={
            "api": "finnhub",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "tickers": ",".join(settings.tickers),
        },
    )

    events = fetch_finnhub_earnings(start, end, settings.api_key)
    selected_events = filter_events(events, settings.tickers)
    cal = build_calendar(selected_events, settings.calendar_name)
    out_path = write_text_file(settings.ics_path, cal.serialize())

    logger.info("ics_written", extra={"path": str(out_path), "events_total": len(selected_events)})


def cli() -> None:
    try:
        configure_logging()
        _run()
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("cli_unhandled_exception", exc_info=exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli()
