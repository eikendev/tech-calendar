"""
API key resolution helpers.
"""

from os import getenv

import structlog


def resolve_api_key(
    *,
    configured: str | None,
    env_fallback: str,
    logger: structlog.stdlib.BoundLogger,
) -> str:
    """
    Resolve an API key from configuration or environment variables.
    """
    api_key = configured or getenv(env_fallback)

    if not api_key:
        logger.error("api_key_missing")
        raise SystemExit(2)

    return api_key
