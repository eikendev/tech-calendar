"""
Main orchestration flow to query AI, update storage, and generate the calendar.
"""

from collections.abc import Iterable
from datetime import date
from pathlib import Path

from tech_calendar.calendar import CalendarMetadata, build_and_write_calendar, make_all_day_event
from tech_calendar.config import AppConfig, SeriesConfig
from tech_calendar.events.models import LookupResult, Occurrence, Series
from tech_calendar.events.researcher import AgentDependencies, Researcher
from tech_calendar.exceptions import OrchestrationError
from tech_calendar.logging import get_logger
from tech_calendar.storage import Database, EventRepository, StoredOccurrence

logger = get_logger(__name__)


def run(config: AppConfig, *, today: date | None = None) -> Path:
    """
    Execute a full run and return the path to the generated ICS file.
    """
    reference_date = today or date.today()
    db_path = config.storage.db_path
    series_map = _build_series(config.events.series)
    researcher = Researcher(config.llm.model)

    with Database(db_path) as db:
        repo = EventRepository(db.connection)

        for series in series_map.values():
            for target_year in (reference_date.year, reference_date.year + 1):
                try:
                    deps = AgentDependencies(
                        series_name=series.name,
                        series_id=series.id,
                        queries=series.queries,
                        year=target_year,
                    )
                    lookup = researcher.fetch(deps)
                    stored = repo.fetch_occurrence(series.id, target_year)
                    merged = _merge_occurrence(series, lookup, stored, reference_date, target_year)
                    repo.save_occurrence(merged)
                except Exception as exc:
                    logger.error(
                        "series_processing_failed",
                        extra={"series_id": series.id, "year": target_year, "error": str(exc)},
                    )
                    continue

        calendar_occurrences = _collect_for_calendar(
            repo, series_map, current_year=reference_date.year, retention_years=config.events.calendar.retention_years
        )

    metadata = CalendarMetadata(
        name=config.events.calendar.name,
        relcalid=config.events.calendar.relcalid,
        description=config.events.calendar.description,
    )
    output_path = build_and_write_calendar(
        calendar_occurrences,
        metadata,
        lambda occ, relcalid: make_all_day_event(
            occ.start_date,
            end_date=occ.end_date,
            uid=occ.uid(relcalid),
            name=f"{occ.series.name} {occ.year}",
            description=occ.description(),
        ),
        config.events.calendar.ics_path,
    )
    logger.info("run_complete", extra={"ics_path": str(output_path), "events_total": len(calendar_occurrences)})
    return Path(output_path)


def _build_series(configured: Iterable[SeriesConfig]) -> dict[str, Series]:
    """
    Build the in-memory series map from configuration.
    """
    series_map: dict[str, Series] = {}
    for item in configured:
        series_map[item.id] = Series(
            id=item.id,
            name=item.name,
            queries=tuple(item.queries),
        )
    return series_map


def _merge_occurrence(
    series: Series,
    lookup: LookupResult,
    existing: StoredOccurrence | None,
    reference_date: date,
    target_year: int,
) -> StoredOccurrence:
    """
    Merge lookup data with existing storage following temporal rules.
    """
    if lookup.year != target_year:
        raise OrchestrationError(f"AI returned year {lookup.year} for series {series.id}, expected {target_year}")

    incoming = Occurrence(
        series=series,
        year=lookup.year,
        start_date=lookup.start_date,
        end_date=lookup.end_date,
        location=lookup.location,
        timezone=lookup.timezone,
        confident=lookup.confident,
        confirmed=lookup.confirmed,
        announcement_url=str(lookup.announcement_url) if lookup.announcement_url else None,
        included=False,
    )

    if existing:
        existing_occurrence = Occurrence(
            series=series,
            year=existing.year,
            start_date=existing.start_date,
            end_date=existing.end_date,
            location=existing.location,
            timezone=existing.timezone,
            confident=existing.confident,
            confirmed=existing.confirmed,
            announcement_url=existing.announcement_url,
            included=existing.included,
        )
        if existing_occurrence.is_past(reference_date) and incoming.is_past(reference_date):
            logger.info(
                "occurrence_skipped_past",
                extra={"series_id": series.id, "year": lookup.year},
            )
            return existing

    included = lookup.confident or lookup.confirmed
    if existing and existing.included and not included:
        included = True
        logger.warning(
            "occurrence_retained_due_to_prior_inclusion",
            extra={"series_id": series.id, "year": lookup.year},
        )

    merged_start = lookup.start_date or (existing.start_date if existing else None)
    merged_end = lookup.end_date or (existing.end_date if existing else None)
    merged_location = lookup.location or (existing.location if existing else None)
    merged_timezone = lookup.timezone or (existing.timezone if existing else None)
    merged_announcement = (
        str(lookup.announcement_url) if lookup.announcement_url else (existing.announcement_url if existing else None)
    )

    return StoredOccurrence(
        series_id=series.id,
        year=lookup.year,
        start_date=merged_start,
        end_date=merged_end,
        location=merged_location,
        timezone=merged_timezone,
        confident=lookup.confident,
        confirmed=lookup.confirmed,
        announcement_url=merged_announcement,
        included=included,
    )


def _collect_for_calendar(
    repo: EventRepository,
    series_map: dict[str, Series],
    *,
    current_year: int,
    retention_years: int,
) -> list[Occurrence]:
    """
    Collect occurrences eligible for calendar inclusion.
    """
    stored_occurrences = repo.list_occurrences_for_calendar(current_year=current_year, retention_years=retention_years)
    occurrences: list[Occurrence] = []

    for record in stored_occurrences:
        series = series_map.get(record.series_id)
        if not series:
            logger.warning("series_missing_from_config", extra={"series_id": record.series_id})
            continue
        if not record.start_date or not record.end_date:
            logger.warning(
                "occurrence_excluded_missing_dates",
                extra={"series_id": record.series_id, "year": record.year},
            )
            continue
        occurrences.append(
            Occurrence(
                series=series,
                year=record.year,
                start_date=record.start_date,
                end_date=record.end_date,
                location=record.location,
                timezone=record.timezone,
                confident=record.confident,
                confirmed=record.confirmed,
                announcement_url=record.announcement_url,
                included=record.included,
            )
        )
    return occurrences
