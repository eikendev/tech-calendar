"""
SQLite-backed repository for event series occurrences.
"""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime

from tech_calendar.exceptions import StorageError
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StoredOccurrence:
    """
    Representation of an occurrence persisted in SQLite.
    """

    series_id: str
    year: int
    start_date: date | None
    end_date: date | None
    location: str | None
    timezone: str | None
    confident: bool
    confirmed: bool
    announcement_url: str | None
    included: bool

    def is_past(self, today: date) -> bool:
        """
        Determine whether the occurrence ended before the reference date.
        """
        if self.end_date:
            return self.end_date < today
        if self.start_date:
            return self.start_date < today
        return False


class EventRepository:
    """
    SQLite-backed repository for event series occurrences.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_occurrence(self, occurrence: StoredOccurrence) -> None:
        """
        Insert or update an occurrence record.
        """
        now = datetime.now(UTC).isoformat()
        try:
            self.conn.execute(
                """
                INSERT INTO occurrences (
                    series_id,
                    year,
                    start_date,
                    end_date,
                    location,
                    timezone,
                    confident,
                    confirmed,
                    announcement_url,
                    included,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(series_id, year) DO UPDATE SET
                    start_date=excluded.start_date,
                    end_date=excluded.end_date,
                    location=excluded.location,
                    timezone=excluded.timezone,
                    confident=excluded.confident,
                    confirmed=excluded.confirmed,
                    announcement_url=excluded.announcement_url,
                    included=excluded.included,
                    updated_at=excluded.updated_at
                """,
                (
                    occurrence.series_id,
                    occurrence.year,
                    _to_iso(occurrence.start_date),
                    _to_iso(occurrence.end_date),
                    occurrence.location,
                    occurrence.timezone,
                    int(occurrence.confident),
                    int(occurrence.confirmed),
                    occurrence.announcement_url,
                    int(occurrence.included),
                    now,
                    now,
                ),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(
                f"failed to persist occurrence for {occurrence.series_id} {occurrence.year}: {exc}"
            ) from exc

    def fetch_occurrence(self, series_id: str, year: int) -> StoredOccurrence | None:
        """
        Retrieve an occurrence by series and year.
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT
                    series_id,
                    year,
                    start_date,
                    end_date,
                    location,
                    timezone,
                    confident,
                    confirmed,
                    announcement_url,
                    included
                FROM occurrences
                WHERE series_id = ? AND year = ?
                """,
                (series_id, year),
            )
            row = cursor.fetchone()
        except sqlite3.Error as exc:
            raise StorageError(f"failed to fetch occurrence for {series_id} {year}: {exc}") from exc

        if not row:
            return None

        return _row_to_occurrence(row)

    def list_occurrences_for_calendar(self, *, current_year: int, retention_years: int) -> list[StoredOccurrence]:
        """
        Return occurrences that should be considered for calendar generation.
        """
        threshold_year = current_year - retention_years
        try:
            cursor = self.conn.execute(
                """
                SELECT
                    series_id,
                    year,
                    start_date,
                    end_date,
                    location,
                    timezone,
                    confident,
                    confirmed,
                    announcement_url,
                    included
                FROM occurrences
                WHERE year >= ? AND included = 1
                """,
                (threshold_year,),
            )
            rows = cursor.fetchall()
        except sqlite3.Error as exc:
            raise StorageError(f"failed to query occurrences for calendar: {exc}") from exc

        return [_row_to_occurrence(row) for row in rows]


def _row_to_occurrence(row: tuple) -> StoredOccurrence:
    """
    Convert a SQLite row into a StoredOccurrence.
    """
    start_raw, end_raw = row[2], row[3]
    return StoredOccurrence(
        series_id=row[0],
        year=int(row[1]),
        start_date=_parse_date(start_raw),
        end_date=_parse_date(end_raw),
        location=row[4],
        timezone=row[5],
        confident=bool(row[6]),
        confirmed=bool(row[7]),
        announcement_url=row[8],
        included=bool(row[9]),
    )


def _parse_date(value: str | None) -> date | None:
    """
    Parse an ISO date string into a date object.
    """
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _to_iso(value: date | None) -> str | None:
    """
    Convert a date to its ISO string representation.
    """
    if value is None:
        return None
    return value.isoformat()
