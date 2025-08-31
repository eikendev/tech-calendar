from datetime import date as date_type
from datetime import datetime, time
from zoneinfo import ZoneInfo

from ics import Calendar, Event
from ics.grammar.parse import ContentLine

from .constants import CALENDAR_DISCLAIMER, CALENDAR_RELCALID, EXCHANGE_TZ
from .models import EarningsEvent


def build_calendar(events: list[EarningsEvent], calendar_name: str) -> Calendar:
    cal = Calendar()
    cal.extra.append(ContentLine(name="X-WR-CALNAME", value=calendar_name))
    cal.extra.append(ContentLine(name="X-WR-RELCALID", value=CALENDAR_RELCALID))
    cal.extra.append(ContentLine(name="X-WR-CALDESC", value=CALENDAR_DISCLAIMER))

    for ev in events:
        e = Event()
        e.name = ev.name()
        e.uid = ev.uid()
        e.begin = _all_day_begin_local(ev.date)
        e.make_all_day()
        e.description = ev.description()
        cal.events.add(e)

    return cal


def _all_day_begin_local(d: date_type) -> datetime:
    return datetime.combine(d, time.min).replace(tzinfo=ZoneInfo(EXCHANGE_TZ))
