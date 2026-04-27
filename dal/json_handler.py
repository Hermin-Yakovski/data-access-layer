import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .abc import DataHandler


class JsonHandler(DataHandler):
    """Handler for JSON format files.

    Supports fetching and storing data in JSON format with optional
    encoding and indentation configuration.
    """

    def __init__(self, encoding: str = 'utf-8', indent: int = 2):
        """Initialize JsonHandler.

        Args:
            encoding: Character encoding for file operations (default: utf-8)
            indent: Number of spaces for JSON indentation (default: 2)
        """
        self.encoding = encoding
        self.indent = indent

    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from JSON file.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            with open(file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(f"JSON file must contain a list of objects, got {type(data).__name__}")

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

        except Exception as e:
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
        """Store data to JSON file.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table

            # Prepare data to store
            data_to_store = data.copy()

            # Apply column selection
            if cols is not None:
                cols_set = set(cols)
                data_to_store = [{k: v for k, v in row.items() if k in cols_set} for row in data_to_store]

            # Apply filtering
            if filter_ is not None:
                data_to_store = [row for row in data_to_store if filter_(row)]

            # Apply limit (after filtering)
            if limit is not None:
                data_to_store = data_to_store[:limit]

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                with open(file_path, 'r', encoding=self.encoding) as f:
                    existing_data = json.load(f)
                if isinstance(existing_data, list):
                    data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, 'w', encoding=self.encoding) as f:
                json.dump(data_to_store, f, indent=self.indent, ensure_ascii=False)

            return len(data_to_store)

        except Exception as e:
            if strict:
                raise
            return 0
