import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .abc import DataHandler


class SqliteHandler(DataHandler):
    """Handler for SQLite databases.

    Supports fetching and storing data in SQLite tables.
    Table must exist before storing data.
    """

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
            path: Path to the SQLite database file
            table: Table name to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if cursor.fetchone() is None:
                conn.close()
                raise Exception(f"Table '{table}' does not exist in database '{path}'")

            # Fetch all data
            cursor.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]

            # Apply column selection
            if cols is not None:
                cols_set = set(cols)
                data = [{k: v for k, v in row.items() if k in cols_set} for row in data]

            # Apply filtering
            if filter_ is not None:
                data = [row for row in data if filter_(row)]

            # Apply limit (after filtering)
            if limit is not None:
                data = data[:limit]

            return data

        except Exception:
            if strict:
                raise
            return []

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
            path: Path to the SQLite database file
            table: Table name to store to (must exist)
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, DELETE existing rows; if False, append
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if cursor.fetchone() is None:
                conn.close()
                raise Exception(f"Table '{table}' does not exist in database '{path}'")

            # Get table columns
            cursor.execute(f"PRAGMA table_info({table})")
            table_columns = {row[1] for row in cursor.fetchall()}

            # Prepare data to store
            data_to_store = data.copy()

            # Apply column selection
            if cols is not None:
                cols_set = set(cols)
                data_to_store = [
                    {k: v for k, v in row.items() if k in cols_set} for row in data_to_store
                ]

            # Apply filtering
            if filter_ is not None:
                data_to_store = [row for row in data_to_store if filter_(row)]

            # Apply limit (after filtering)
            if limit is not None:
                data_to_store = data_to_store[:limit]

            # Clear table if overwrite mode
            if overwrite:
                cursor.execute(f"DELETE FROM {table}")

            # Insert data
            if data_to_store:
                # Only insert columns that exist in table
                for row in data_to_store:
                    columns_to_insert = [k for k in row.keys() if k in table_columns]
                    if not columns_to_insert:
                        continue
                    placeholders = ", ".join(["?"] * len(columns_to_insert))
                    columns_str = ", ".join(columns_to_insert)
                    values = [row.get(col) for col in columns_to_insert]
                    cursor.execute(
                        f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                        values
                    )

            conn.commit()
            conn.close()

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
