"""
Domain models for earnings processing.
"""

from dataclasses import dataclass
from datetime import date
from hashlib import sha256

from tech_calendar.constants import DEFAULT_EARNINGS_RELCALID, UID_VERSION
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EarningsEvent:
    """
    Earnings event representation used for persistence and calendar output.
    """

    ticker: str
    date: date
    quarter: int
    fiscal_year: int | None = None
    eps_estimate: float | None = None
    revenue_estimate: float | None = None
    source: str | None = None

    def event_year(self) -> int:
        """
        Return the fiscal year if provided, falling back to the calendar year.
        """
        return self.fiscal_year if self.fiscal_year is not None else self.date.year

    def uid(self, relcalid: str = DEFAULT_EARNINGS_RELCALID) -> str:
        """
        Generate a deterministic UID for the earnings event.
        """
        digest = sha256(
            f"{UID_VERSION}|earnings|{self.ticker.lower()}|{self.event_year()}|{self.quarter}".encode()
        ).hexdigest()
        return f"{UID_VERSION}-{digest}@{relcalid}"

    def name(self) -> str:
        """
        Build the event name.
        """
        return f"{self.ticker} Q{self.quarter} Earnings"

    def description(self) -> str:
        """
        Build the multi-line description for the ICS entry.
        """
        details = [
            f"Ticker: {self.ticker}",
            f"Fiscal Qtr: {self.quarter or '-'}",
            f"Estimate EPS: {self.eps_estimate if self.eps_estimate is not None else '-'}",
            f"Est. Revenue: {_format_revenue(self.revenue_estimate)}",
            f"Source: {self.source or '-'}",
        ]
        return "\n".join(details)


def _format_revenue(value: float | int | str | None) -> str:
    """
    Format a revenue figure into a compact human-readable string.
    """
    if value is None:
        return "-"

    try:
        n = float(value)
    except (TypeError, ValueError):
        return "-"

    if n < 0:
        logger.warning(
            "negative_revenue_provided",
            extra={"value": n},
        )
        return "-"

    n = round(n)

    if n < 1_000:
        return f"{n:.0f}"
    if n < 1_000_000:
        return f"{(n / 1_000):.0f} K"
    if n < 1_000_000_000:
        return f"{(n / 1_000_000):.1f} M"
    if n < 1_000_000_000_000:
        return f"{(n / 1_000_000_000):.2f} B"
    return f"{(n / 1_000_000_000_000):.2f} T"
