"""
Shared constants for tech-calendar.
"""

from pathlib import Path

EXCHANGE_TZ: str = "America/New_York"

DEFAULT_DB_PATH: Path = Path("tech_calendar.db")

CLI_ENV_PREFIX: str = "TC"
ENV_FINNHUB_API_KEY: str = "TC_FINNHUB_API_KEY"

DEFAULT_EARNINGS_RELCALID: str = "tech.calendar.earnings"
DEFAULT_EARNINGS_CALENDAR_NAME: str = "Tech Earnings Calendar"
DEFAULT_EARNINGS_CALENDAR_DESCRIPTION: str = (
    "No representation or warranty, express or implied, is made as to the accuracy, "
    "completeness, or timeliness of this information. Do not rely on this calendar "
    "or its contents for investment or trading decisions."
)
DEFAULT_EARNINGS_ICS_PATH: Path = Path("earnings.ics")
DEFAULT_EARNINGS_RETENTION_YEARS: int = 5
DEFAULT_EARNINGS_DAYS_AHEAD: int = 20
DEFAULT_EARNINGS_DAYS_PAST: int = 10

UID_VERSION: str = "v1"
