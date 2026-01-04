"""
Logging configuration for the tech-calendar application.
"""

import logging
import sys

import structlog

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging(log_level_str: str = "INFO") -> None:
    """
    Configure standard logging and structlog for structured output.
    """
    level_key = log_level_str.upper()
    if level_key not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {log_level_str}")

    log_level = LOG_LEVELS[level_key]

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=log_level,
    )

    for logger_name in logging.root.manager.loggerDict:
        if not logger_name.startswith("tech_calendar"):
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a structured logger bound to the given name.
    """
    return structlog.get_logger(name)
