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
        raise NotImplementedError("store() method not yet implemented")
