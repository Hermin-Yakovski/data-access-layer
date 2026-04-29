import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .abc import DataHandler


class SqliteHandler(DataHandler):
    """Handler for SQLite databases.

    Supports fetching and storing data in SQLite tables.
    Table must exist before storing data.
    """

    def __init__(self, path: Path):
        """Initialize SqliteHandler.

        Args:
            path: Path to the SQLite database file
        """
        self.path = path

    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from SQLite table.

        Args:
            path: Not used (path set in __init__)
            table: Table name to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries
        """
        raise NotImplementedError("fetch() method not yet implemented")

    def store(
        self,
        data: List[Dict[str, Any]],
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        overwrite: bool = True,
        strict: bool = True,
    ) -> int:
        """Store data to SQLite table.

        Args:
            data: List of row dictionaries to store
            path: Not used (path set in __init__)
            table: Table name to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing data; if False, append
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored
        """
        raise NotImplementedError("store() method not yet implemented")
