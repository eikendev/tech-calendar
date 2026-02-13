"""YAML configuration loader for tech-calendar."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from tech_calendar.config.models import AppConfig, StorageConfig
from tech_calendar.constants import CONFIG_DIR_NAME, DEFAULT_CONFIG_CANDIDATES, ENV_DB_PATH
from tech_calendar.exceptions import ConfigError
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file into a mapping."""
    logger.debug("config_read_start", path=str(path))
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Failed to read config file: {path}") from exc

    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file: {path}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ConfigError(f"Config file must be a YAML mapping: {path}")

    logger.info("config_read_success", path=str(path))
    return data


def _xdg_config_home() -> Path:
    """Return the XDG config directory."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")

    if xdg_config_home:
        return Path(xdg_config_home).expanduser()

    return Path.home() / ".config"


def _iter_config_paths() -> Iterator[Path]:
    """Return candidate config paths in priority order."""
    base = Path.cwd()
    xdg_root = _xdg_config_home() / CONFIG_DIR_NAME
    etc_root = Path("/etc") / CONFIG_DIR_NAME

    logger.debug(
        "config_search_roots",
        cwd=str(base),
        xdg_root=str(xdg_root),
        etc_root=str(etc_root),
        candidates=list(DEFAULT_CONFIG_CANDIDATES),
    )

    for dir in (xdg_root, base, etc_root):
        for name in DEFAULT_CONFIG_CANDIDATES:
            candidate = (dir / name).expanduser().resolve()
            logger.debug("config_search_candidate", path=str(candidate))
            yield candidate


def _load_config_from_file(path: Path) -> AppConfig:
    """Load and validate configuration from a YAML file path."""
    data = _read_yaml(path)

    try:
        config = AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration in {path}: {exc}") from exc

    logger.info("Loaded config", path=str(path))
    return config


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    """Apply environment variable overrides to configuration."""
    env_db_path = os.environ.get(ENV_DB_PATH)
    if not env_db_path:
        return config

    try:
        storage = StorageConfig.model_validate({"db_path": env_db_path})
    except ValidationError as exc:
        raise ConfigError(f"Invalid {ENV_DB_PATH} value: {exc}") from exc

    logger.info("config_env_override", key=ENV_DB_PATH)
    return config.model_copy(update={"storage": storage})


def find_config_file(config_path: Path | None = None) -> Path:
    """Return the first available configuration file path."""
    if config_path is not None:
        resolved = config_path.expanduser().resolve()
        logger.debug("config_explicit_path", path=str(resolved))
        if resolved.is_file():
            logger.info("config_file_found", path=str(resolved), source="explicit")
            return resolved

        if resolved.exists():
            logger.debug("config_path_not_file", path=str(resolved))
            raise ConfigError(f"Config path is not a file: {resolved}")

        logger.debug("config_path_missing", path=str(resolved))
        raise ConfigError(f"Config file does not exist: {resolved}")

    for path in _iter_config_paths():
        if path.is_file():
            logger.info("config_file_found", path=str(path), source="search")
            return path

        if path.exists():
            logger.debug("config_path_not_file", path=str(path))
            raise ConfigError(f"Config path is not a file: {path}")

        logger.debug("config_path_missing", path=str(path))

    raise ConfigError("No valid configuration file found.")


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load the tech-calendar YAML configuration."""
    resolved_path = find_config_file(config_path)
    config = _load_config_from_file(resolved_path)
    return _apply_env_overrides(config)
