"""
Generic helpers to build and write ICS calendars.
"""

from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ics import Calendar, Event
from ics.grammar.parse import ContentLine

from tech_calendar.constants import EXCHANGE_TZ
from tech_calendar.file_utils import write_text_file


@dataclass(frozen=True)
class CalendarMetadata:
    """
    Metadata applied to the top-level calendar.
    """

    name: str
    relcalid: str
    description: str


def build_calendar(items: list, metadata: CalendarMetadata, event_builder) -> Calendar:
    """
    Build an ICS calendar from arbitrary items using the provided event builder.
    """
    calendar = Calendar()
    calendar.extra.append(ContentLine(name="X-WR-CALNAME", value=metadata.name))
    calendar.extra.append(ContentLine(name="X-WR-RELCALID", value=metadata.relcalid))
    calendar.extra.append(ContentLine(name="X-WR-CALDESC", value=metadata.description))

    for item in items:
        event = event_builder(item, metadata.relcalid)
        calendar.events.add(event)

    return calendar


def build_and_write_calendar(items: list, metadata: CalendarMetadata, event_builder, path: Path) -> str:
    """
    Build a calendar and write it to disk.
    """
    calendar = build_calendar(items, metadata, event_builder)
    out_path = write_text_file(path, calendar.serialize())
    return str(out_path)


def make_all_day_event(
    start_date: date_type, *, uid: str, name: str, description: str, end_date: date_type | None = None
) -> Event:
    """
    Create an all-day event. If end_date is provided, span inclusively.
    """
    event = Event()
    event.uid = uid
    event.name = name
    if end_date and end_date != start_date:
        event.begin, event.end = _all_day_bounds(start_date, end_date)
    else:
        event.begin = _all_day_begin_local(start_date)
    event.make_all_day()
    event.description = description
    return event


def _all_day_begin_local(d: date_type) -> datetime:
    return datetime.combine(d, time.min).replace(tzinfo=ZoneInfo(EXCHANGE_TZ))


def _all_day_bounds(start: date_type, end: date_type) -> tuple[datetime, datetime]:
    begin_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end + timedelta(days=1), time.min)
    return begin_dt, end_dt
