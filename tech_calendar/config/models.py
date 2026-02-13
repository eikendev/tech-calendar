"""
Configuration models for tech-calendar.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from tech_calendar.constants import (
    DEFAULT_DB_PATH,
    DEFAULT_EARNINGS_CALENDAR_DESCRIPTION,
    DEFAULT_EARNINGS_CALENDAR_NAME,
    DEFAULT_EARNINGS_DAYS_AHEAD,
    DEFAULT_EARNINGS_DAYS_PAST,
    DEFAULT_EARNINGS_ICS_PATH,
    DEFAULT_EARNINGS_RELCALID,
    DEFAULT_EARNINGS_RETENTION_YEARS,
)


class StorageConfig(BaseModel):
    """
    Settings for persistent SQLite storage.
    """

    db_path: Path = Field(default=DEFAULT_DB_PATH)


class CalendarBase(BaseModel):
    """
    Shared calendar configuration fields.
    """

    ics_path: Path
    relcalid: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    retention_years: Annotated[int, Field(ge=1, le=50)]


class EarningsCalendarConfig(CalendarBase):
    """
    Calendar settings for earnings output.
    """

    ics_path: Path = Field(default=DEFAULT_EARNINGS_ICS_PATH)
    relcalid: str = Field(default=DEFAULT_EARNINGS_RELCALID, min_length=1)
    name: str = Field(default=DEFAULT_EARNINGS_CALENDAR_NAME, min_length=1)
    description: str = Field(default=DEFAULT_EARNINGS_CALENDAR_DESCRIPTION, min_length=1)
    retention_years: Annotated[int, Field(ge=1, le=50)] = DEFAULT_EARNINGS_RETENTION_YEARS


class EarningsConfig(BaseModel):
    """
    Configuration for earnings calendar generation.
    """

    calendar: EarningsCalendarConfig = Field(default_factory=EarningsCalendarConfig)
    days_ahead: Annotated[int, Field(ge=0, le=365)] = DEFAULT_EARNINGS_DAYS_AHEAD
    days_past: Annotated[int, Field(ge=0, le=365)] = DEFAULT_EARNINGS_DAYS_PAST
    tickers: list[str] = Field(default_factory=list, min_length=1)
    api_key: str | None = None

    @field_validator("tickers")
    @classmethod
    def _normalize_tickers(cls, value: Iterable[str]) -> list[str]:
        parsed = [item.strip().upper() for item in value if item and str(item).strip()]
        if not parsed:
            raise ValueError("tickers must not be empty")
        return parsed


class AppConfig(BaseModel):
    """
    Root configuration for earnings.
    """

    storage: StorageConfig = Field(default_factory=StorageConfig)
    earnings: EarningsConfig
