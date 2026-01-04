"""
Agent that retrieves structured occurrence data for event series.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from pydantic_ai import Agent, WebSearchTool
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tech_calendar.events.models import LookupResult
from tech_calendar.exceptions import LLMError
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentDependencies:
    """
    Context passed to the agent for each query.
    """

    series_name: str
    series_id: str
    queries: Sequence[str]
    year: int


class Researcher:
    """
    Thin wrapper over pydantic-ai to retrieve structured event data.
    """

    def __init__(self, model: str):
        self.agent = Agent(
            model,
            output_type=LookupResult,
            deps_type=AgentDependencies,
            system_prompt=_SYSTEM_PROMPT,
            builtin_tools=[WebSearchTool()],
        )
        self.model = model

    def fetch(self, deps: AgentDependencies) -> LookupResult:
        """
        Query the LLM model for a specific series and year.
        """
        logger.info(
            "llm_query_start",
            extra={
                "series_id": deps.series_id,
                "year": deps.year,
                "model": self.model,
            },
        )
        try:
            result = self._run_with_retry(deps)
        except Exception as exc:
            logger.error(
                "llm_query_failed",
                extra={"series_id": deps.series_id, "year": deps.year, "error": str(exc)},
            )
            raise LLMError(str(exc)) from exc

        logger.info(
            "llm_query_success",
            extra={
                "series_id": deps.series_id,
                "year": deps.year,
                "confident": result.confident,
                "confirmed": result.confirmed,
                "has_dates": bool(result.start_date and result.end_date),
            },
        )
        return result

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _run_with_retry(self, deps: AgentDependencies) -> LookupResult:
        """
        Execute the LLM lookup with bounded retries.
        """
        prompt = _build_prompt(deps)
        outcome = self.agent.run_sync(prompt, deps=deps, output_type=LookupResult)
        return outcome.output


def _build_prompt(deps: AgentDependencies) -> str:
    """
    Build the structured prompt for the LLM lookup.
    """
    queries = "; ".join(deps.queries)
    today = date.today().isoformat()
    return (
        "You aggregate structured information about annually recurring technology events.\n"
        "Consult multiple independent public sources and prefer authoritative announcements when available.\n"
        f"Today is {today}.\n"
        f"Series name: {deps.series_name}\n"
        f"Series id: {deps.series_id}\n"
        f"Target year: {deps.year}\n"
        f"Search queries to consider: {queries}\n"
        "Return structured data with these fields:\n"
        "- year (integer)\n"
        "- start_date (YYYY-MM-DD or null if not announced)\n"
        "- end_date (YYYY-MM-DD or null if not announced)\n"
        "- location (city or venue, optional)\n"
        "- timezone (IANA TZ, optional)\n"
        "- confident (true if multiple independent sources agree)\n"
        "- confirmed (true if an official announcement exists)\n"
        "- announcement_url (URL of the announcement if available)\n"
        "If no dates are known yet, set start_date and end_date to null but keep other fields if available."
    )


_SYSTEM_PROMPT = (
    "You are a meticulous researcher that only returns structured data. "
    "Never speculate beyond public information, avoid hallucinating dates, and prefer authoritative sources."
)
