"""
Command-line interface for tech-calendar.
"""

from datetime import date
from pathlib import Path
from typing import Protocol

import click

from tech_calendar.config import AppConfig, find_config_file, load_config
from tech_calendar.constants import CLI_ENV_PREFIX
from tech_calendar.earnings.runner import run_earnings
from tech_calendar.events.runner import run as run_events
from tech_calendar.exceptions import ConfigError, OrchestrationError, StorageError
from tech_calendar.logging import configure_logging, get_logger

logger = get_logger(__name__)

LOG_LEVEL_CHOICES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class CommandAction(Protocol):
    """
    Callable protocol for CLI actions.
    """

    def __call__(self, config: AppConfig, *, today: date | None = None) -> Path | None: ...


def _execute_command(action: CommandAction, config: AppConfig) -> None:
    """
    Execute a CLI action with consistent error handling.
    """
    try:
        action(config)
    except (ConfigError, StorageError, OrchestrationError) as exc:
        logger.error("cli_validation_error", error=str(exc))
        raise SystemExit(2) from exc
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("cli_unhandled_exception", exc_info=exc)
        raise SystemExit(1) from exc


@click.group(context_settings={"auto_envvar_prefix": CLI_ENV_PREFIX})
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to the YAML configuration file.",
)
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVEL_CHOICES, case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Logging level.",
)
@click.pass_context
def cli(ctx: click.Context, log_level: str, config_file: Path | None) -> None:
    try:
        configure_logging(log_level)
        resolved_config = find_config_file(config_file)
        ctx.ensure_object(dict)
        ctx.obj["config"] = load_config(resolved_config)
    except (ConfigError, StorageError, OrchestrationError, ValueError) as exc:
        logger.error("cli_validation_error", error=str(exc))
        raise SystemExit(2) from exc
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("cli_unhandled_exception", exc_info=exc)
        raise SystemExit(1) from exc


@cli.command()
@click.pass_context
def earnings(ctx: click.Context) -> None:
    """
    Generate the earnings calendar from Finnhub data.
    """
    _execute_command(run_earnings, ctx.obj["config"])


@cli.command()
@click.pass_context
def events(ctx: click.Context) -> None:
    """
    Generate the annual technology events calendar.
    """
    _execute_command(run_events, ctx.obj["config"])


if __name__ == "__main__":
    cli()
