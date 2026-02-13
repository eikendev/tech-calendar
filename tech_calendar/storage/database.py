"""
SQLite connection management and schema initialization.
"""

import sqlite3
from pathlib import Path

from pydantic import AnyUrl

from tech_calendar.exceptions import StorageError
from tech_calendar.logging import get_logger
from tech_calendar.storage.backends import StorageBackend

logger = get_logger(__name__)


class Database:
    """
    Manage the shared SQLite connection and schema.
    """

    def __init__(self, db_path: AnyUrl):
        """
        Initialize the database connection using the configured storage backend.
        """
        self.location = db_path
        self.backend = StorageBackend.from_location(db_path)
        self.db_path = self.backend.prepare()
        self.conn = self._open(self.db_path)
        self._ensure_schema()

    def close(self) -> None:
        """
        Close the database connection and persist backend changes.
        """
        try:
            self.conn.close()
        except sqlite3.Error:
            logger.warning("db_close_failed", extra={"path": str(self.db_path)})

        self.backend.finalize()

    def __enter__(self) -> "Database":
        """
        Enter the database context manager.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Exit the database context manager and close resources.
        """
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Expose the underlying SQLite connection.
        """
        return self.conn

    @staticmethod
    def _open(db_path: Path) -> sqlite3.Connection:
        """
        Open the SQLite connection for the given local path.
        """
        try:
            return sqlite3.connect(str(db_path))
        except sqlite3.Error as exc:
            raise StorageError(f"failed to open database at {db_path}: {exc}") from exc

    def _ensure_schema(self) -> None:
        """
        Ensure the SQLite schema exists.
        """
        try:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS earnings (
                    ticker TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    event_date TEXT NOT NULL,
                    eps_estimate REAL,
                    revenue_estimate REAL,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (ticker, fiscal_year, quarter)
                )
                """
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"failed to initialize schema: {exc}") from exc
