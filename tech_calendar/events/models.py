"""
Domain and lookup models for annual events.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Annotated, Any

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from tech_calendar.constants import DEFAULT_EVENTS_RELCALID, UID_VERSION


def occurrence_uid(series_id: str, year: int, relcalid: str = DEFAULT_EVENTS_RELCALID) -> str:
    """
    Compute a deterministic UID for an occurrence.
    """
    digest = sha256(f"{UID_VERSION}|events|{series_id}|{year}".encode()).hexdigest()
    return f"{UID_VERSION}-{digest}@{relcalid}"


@dataclass(frozen=True)
class Series:
    """
    A logical annual event series defined in configuration.
    """

    id: str
    name: str
    queries: tuple[str, ...]


@dataclass
class Occurrence:
    """
    A single annual occurrence of a series.
    """

    series: Series
    year: int
    start_date: date | None
    end_date: date | None
    location: str | None
    timezone: str | None
    confident: bool
    confirmed: bool
    announcement_url: str | None
    included: bool

    def uid(self, relcalid: str | None = None) -> str:
        """
        Return the deterministic UID for this occurrence.
        """
        return occurrence_uid(self.series.id, self.year, relcalid or DEFAULT_EVENTS_RELCALID)

    def is_past(self, today: date, *, now_provider: Callable[[], date] | None = None) -> bool:
        """
        Determine whether the occurrence is entirely in the past.
        """
        reference = now_provider() if now_provider else today
        if self.end_date:
            return self.end_date < reference
        if self.start_date:
            return self.start_date < reference
        return False

    def description(self) -> str:
        """
        Build the multi-line description for the ICS entry.
        """
        lines = [
            f"Series: {self.series.name}",
            f"Year: {self.year}",
            f"Confirmed: {self.confirmed}",
            f"Confident: {self.confident}",
        ]
        if self.location:
            lines.append(f"Location: {self.location}")
        if self.timezone:
            lines.append(f"Timezone (informational): {self.timezone}")
        if self.announcement_url:
            lines.append(f"Announcement: {self.announcement_url}")
        return "\n".join(lines)


class LookupResult(BaseModel):
    """
    Structured occurrence data returned by the agent.
    """

    year: Annotated[int, Field(ge=1970, le=2100)]
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    timezone: str | None = None
    confident: bool = False
    confirmed: bool = False
    announcement_url: HttpUrl | None = None

    @field_validator("location", "timezone", mode="before")
    @classmethod
    def _clean_strings(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @model_validator(mode="after")
    def _validate_dates(self) -> "LookupResult":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")

        if self.start_date and self.year != self.start_date.year:
            raise ValueError("year must match start_date")

        if not self.start_date and self.end_date:
            raise ValueError("end_date requires start_date")

        if self.start_date and not self.end_date:
            self.end_date = self.start_date

        return self
