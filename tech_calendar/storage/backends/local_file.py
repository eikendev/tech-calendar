"""
Local filesystem storage backend.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

from pydantic import AnyUrl

from tech_calendar.exceptions import StorageError
from tech_calendar.storage.backends.base import StorageBackend


class LocalFileBackend(StorageBackend):
    """
    Storage backend for local filesystem paths.
    """

    scheme = "file"

    def __init__(self, location: AnyUrl) -> None:
        """
        Parse a local file location into a filesystem path.
        """
        super().__init__(location)
        self._path = self._parse_location(location)

    def prepare(self) -> Path:
        """
        Return the local filesystem path for SQLite storage.
        """
        return self._path

    def finalize(self) -> None:
        """
        No-op for local filesystem storage.
        """
        return None

    @staticmethod
    def _parse_location(location: AnyUrl) -> Path:
        """
        Parse a file URL or raw path into a filesystem Path.
        """
        if location.scheme != "file":
            raise StorageError(f"invalid file storage scheme: {location.scheme}")

        host = unquote(location.host) if location.host else ""
        path = unquote(location.path or "")

        path_value = (host if path in ("", "/") else f"{host}{path}") if host else path

        if path_value.endswith("/") and path_value != "/":
            path_value = path_value.rstrip("/")

        if not path_value or path_value == "/":
            raise StorageError("file storage path is empty")

        return Path(path_value).expanduser()
