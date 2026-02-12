"""
SQLite connection management and schema initialization.
"""

import sqlite3
from pathlib import Path

from tech_calendar.exceptions import StorageError
from tech_calendar.logging import get_logger

logger = get_logger(__name__)


class Database:
    """
    Manage the shared SQLite connection and schema.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn = self._open(self.db_path)
        self._ensure_schema()

    def close(self) -> None:
        try:
            self.conn.close()
        except sqlite3.Error:
            logger.warning("db_close_failed", extra={"path": str(self.db_path)})

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Expose the underlying SQLite connection.
        """
        return self.conn

    @staticmethod
    def _open(db_path: Path) -> sqlite3.Connection:
        try:
            return sqlite3.connect(str(db_path))
        except sqlite3.Error as exc:
            raise StorageError(f"failed to open database at {db_path}: {exc}") from exc

    def _ensure_schema(self) -> None:
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
