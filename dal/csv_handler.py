import aiofiles
import csv
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import AsyncDataHandler, DataHandler
from .post_processing import PostProcessingMixin


class CsvHandler(PostProcessingMixin, DataHandler):
    """Handler for CSV format files.

    Supports fetching and storing data in CSV format with optional
    delimiter and encoding configuration.
    """

    def __init__(self, delimiter: str = ",", encoding: str = "utf-8"):
        """Initialize CsvHandler.

        Args:
            delimiter: Character used to separate fields (default: ',')
            encoding: Character encoding for file operations (default: utf-8)
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch data from CSV file.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            with open(file_path, "r", encoding=self.encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                data = list(reader)

            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)

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
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to CSV file.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table

            # Prepare data to store
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            # Determine fieldnames from data
            if data_to_store:
                fieldnames = list(data_to_store[0].keys())
            else:
                fieldnames = []

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                existing_data = []
                with open(file_path, "r", encoding=self.encoding, newline="") as f:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    existing_data = list(reader)
                data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, "w", encoding=self.encoding, newline="") as f:
                if data_to_store:
                    fieldnames = list(data_to_store[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
                    writer.writeheader()
                    writer.writerows(data_to_store)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0


class AsyncCsvHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for CSV format files."""

    def __init__(self, delimiter: str = ",", encoding: str = "utf-8"):
        """Initialize AsyncCsvHandler.

        Args:
            delimiter: Character used to separate fields (default: ',')
            encoding: Character encoding for file operations (default: utf-8)
        """
        self.delimiter = delimiter
        self.encoding = encoding

    async def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch data from CSV file asynchronously.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            async with aiofiles.open(file_path, "r", encoding=self.encoding, newline="") as f:
                content = await f.read()

            reader = csv.DictReader(StringIO(content), delimiter=self.delimiter)
            data = list(reader)

            data = self._apply_processing(data, types, cols, filter_, limit)
            return data
        except Exception:
            if strict:
                raise
            return []

    async def store(
        self,
        data: List[Dict[str, Any]],
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        overwrite: bool = True,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to CSV file asynchronously.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            if not data_to_store:
                return 0

            fieldnames = list(data_to_store[0].keys())

            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data_to_store)
            content = output.getvalue()

            async with aiofiles.open(file_path, "w", encoding=self.encoding, newline="") as f:
                await f.write(content)

            return len(data_to_store)
        except Exception:
            if strict:
                raise
            return 0
