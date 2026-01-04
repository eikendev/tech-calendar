"""
Configuration models and loader for tech-calendar.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from tech_calendar.constants import (
    DEFAULT_DB_PATH,
    DEFAULT_EARNINGS_CALENDAR_DESCRIPTION,
    DEFAULT_EARNINGS_CALENDAR_NAME,
    DEFAULT_EARNINGS_DAYS_AHEAD,
    DEFAULT_EARNINGS_DAYS_PAST,
    DEFAULT_EARNINGS_ICS_PATH,
    DEFAULT_EARNINGS_RELCALID,
    DEFAULT_EARNINGS_RETENTION_YEARS,
    DEFAULT_EVENTS_CALENDAR_DESCRIPTION,
    DEFAULT_EVENTS_CALENDAR_NAME,
    DEFAULT_EVENTS_ICS_PATH,
    DEFAULT_EVENTS_RELCALID,
    DEFAULT_EVENTS_RETENTION_YEARS,
    DEFAULT_LLM_MODEL,
)
from tech_calendar.exceptions import ConfigError
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


DEFAULT_CONFIG_PATHS: list[Path] = [
    Path("~/.config/tech-calendar/config.yaml").expanduser(),
    Path("~/.config/tech-calendar/config.yml").expanduser(),
    Path("config.yaml"),
    Path("config.yml"),
    Path("/etc/tech-calendar/config.yaml"),
    Path("/etc/tech-calendar/config.yml"),
]


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


class EventsCalendarConfig(CalendarBase):
    """
    Settings for event calendar output.
    """

    ics_path: Path = Field(default=DEFAULT_EVENTS_ICS_PATH)
    relcalid: str = Field(default=DEFAULT_EVENTS_RELCALID, min_length=1)
    name: str = Field(default=DEFAULT_EVENTS_CALENDAR_NAME, min_length=1)
    description: str = Field(default=DEFAULT_EVENTS_CALENDAR_DESCRIPTION, min_length=1)
    retention_years: Annotated[int, Field(ge=1, le=50)] = DEFAULT_EVENTS_RETENTION_YEARS


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


class LLMConfig(BaseModel):
    """
    Settings for LLM-backed operations.
    """

    model: str = Field(default=DEFAULT_LLM_MODEL, min_length=1)


class SeriesConfig(BaseModel):
    """
    Configuration for a single recurring event series.
    """

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    queries: list[str] = Field(..., min_length=1)

    @field_validator("queries")
    @classmethod
    def _normalize_queries(cls, value: Iterable[str]) -> list[str]:
        parsed = [item.strip() for item in value if item and str(item).strip()]
        if not parsed:
            raise ValueError("queries must not be empty")
        return parsed

    @field_validator("id", "name")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be empty")
        return cleaned


class EventsConfig(BaseModel):
    """
    Configuration for annual events processing.
    """

    calendar: EventsCalendarConfig
    series: list[SeriesConfig]

    @model_validator(mode="after")
    def _validate_series(self) -> "EventsConfig":
        ids = [s.id for s in self.series]
        if len(ids) != len(set(ids)):
            raise ValueError("series identifiers must be unique")
        if not self.series:
            raise ValueError("at least one series must be configured")
        return self


class AppConfig(BaseModel):
    """
    Root configuration spanning earnings and events.
    """

    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    earnings: EarningsConfig
    events: EventsConfig


def load_config(path: Path) -> AppConfig:
    """
    Load the application configuration from YAML.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file not found at {path}") from exc
    except OSError as exc:
        raise ConfigError(f"failed to read configuration file at {path}: {exc}") from exc

    try:
        parsed: Any = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"failed to parse YAML at {path}: {exc}") from exc

    try:
        return AppConfig.model_validate(parsed)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


def _config_search_paths(config_option: Path | None = None) -> list[Path]:
    """
    Build the ordered list of configuration paths to probe.
    """
    candidates: list[Path] = []
    if config_option:
        candidates.append(config_option)
    candidates.extend(DEFAULT_CONFIG_PATHS)
    return [path.expanduser().resolve() for path in candidates]


def find_config_file(config_option: Path | None = None) -> Path:
    """
    Return the first available configuration file path.
    """
    search_paths = _config_search_paths(config_option)
    for path in search_paths:
        logger.debug("Checking path for config file", path=str(path))
        if path.is_file():
            logger.debug("Found configuration file", path=str(path))
            return path

    raise ConfigError(f"No valid configuration file found. Checked: {', '.join(str(p) for p in search_paths)}")


def default_config_path() -> Path:
    """
    Return the resolved config path using discovery.
    """
    return find_config_file()
