import aiofiles
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import AsyncDataHandler, DataHandler
from .post_processing import PostProcessingMixin


class JsonHandler(PostProcessingMixin, DataHandler):
    """Handler for JSON format files.

    Supports fetching and storing data in JSON format with optional
    encoding and indentation configuration.
    """

    def __init__(self, encoding: str = "utf-8", indent: int = 2):
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
        types: Optional[Dict[str, Type[Any]]] = None,
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

            with open(file_path, "r", encoding=self.encoding) as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(
                    f"JSON file must contain a list of objects, got {type(data).__name__}"
                )

            # Validate that all items are dictionaries
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSON file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
                    )

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
        types: Optional[Dict[str, Type[Any]]] = None,
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

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                with open(file_path, "r", encoding=self.encoding) as f:
                    existing_data = json.load(f)
                if isinstance(existing_data, list):
                    data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, "w", encoding=self.encoding) as f:
                json.dump(data_to_store, f, indent=self.indent, ensure_ascii=False)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0


class AsyncJsonHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for JSON format files.

    Supports fetching and storing data in JSON format with optional
    encoding and indentation configuration using async I/O.
    """

    def __init__(self, encoding: str = "utf-8", indent: int = 2):
        """Initialize AsyncJsonHandler.

        Args:
            encoding: Character encoding for file operations (default: utf-8)
            indent: Number of spaces for JSON indentation (default: 2)
        """
        self.encoding = encoding
        self.indent = indent

    async def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        types: Optional[Dict[str, Type[Any]]] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from JSON file asynchronously.

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

            async with aiofiles.open(file_path, "r", encoding=self.encoding) as f:
                content = await f.read()
                data = json.loads(content)

            if not isinstance(data, list):
                raise ValueError(
                    f"JSON file must contain a list of objects, got {type(data).__name__}"
                )

            # Validate that all items are dictionaries
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSON file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
                    )

            # Use unified post-processing
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
        types: Optional[Dict[str, Type[Any]]] = None,
        overwrite: bool = True,
        strict: bool = True,
    ) -> int:
        """Store data to JSON file asynchronously.

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

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                async with aiofiles.open(file_path, "r", encoding=self.encoding) as f:
                    content = await f.read()
                    existing_data = json.loads(content)
                if isinstance(existing_data, list):
                    data_to_store = existing_data + data_to_store

            # Write to file
            content = json.dumps(data_to_store, indent=self.indent, ensure_ascii=False)
            async with aiofiles.open(file_path, "w", encoding=self.encoding) as f:
                await f.write(content)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
