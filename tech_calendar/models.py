from dataclasses import dataclass
from datetime import date

from .constants import CALENDAR_RELCALID
from .logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EarningsEvent:
    ticker: str
    date: date
    quarter: int
    eps_estimate: float | None = None
    revenue_estimate: float | None = None
    source: str | None = None

    def uid(self) -> str:
        return f"{self.ticker.lower()}-q{self.quarter}-earnings@{CALENDAR_RELCALID}"

    def name(self) -> str:
        return f"{self.ticker} Q{self.quarter} Earnings"

    def description(self) -> str:
        details = [
            f"Ticker: {self.ticker}",
            f"Fiscal Qtr: {self.quarter or '-'}",
            f"Estimate EPS: {self.eps_estimate if self.eps_estimate is not None else '-'}",
            f"Est. Revenue: {_format_revenue(self.revenue_estimate)}",
            f"Source: {self.source or '-'}",
        ]
        return "\n".join(details)


def _format_revenue(
    value: float | int | str | None,
) -> str:
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
    elif n < 1_000_000:
        return f"{(n / 1_000):.0f} K"
    elif n < 1_000_000_000:
        return f"{(n / 1_000_000):.1f} M"
    elif n < 1_000_000_000_000:
        return f"{(n / 1_000_000_000):.2f} B"
    else:
        return f"{(n / 1_000_000_000_000):.2f} T"
