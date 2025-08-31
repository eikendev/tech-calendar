import os
from dataclasses import dataclass


@dataclass
class Settings:
    tickers: list[str] | None
    ics_path: str
    calendar_name: str
    days_ahead: int
    days_past: int
    api_key: str | None

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            tickers=_csv(os.getenv("TICKERS", None)),
            ics_path=os.getenv("ICS_PATH", "calendar.ics"),
            calendar_name=os.getenv("CALENDAR_NAME", "Tech Calendar"),
            days_ahead=int(os.getenv("DAYS_AHEAD", "20")),
            days_past=int(os.getenv("DAYS_PAST", "10")),
            api_key=os.getenv("API_KEY", None),
        )


def _csv(s: str | None) -> list[str] | None:
    if s is None:
        return None

    return [p.strip() for p in s.split(",") if p.strip()]
