import asyncio
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import AsyncDataHandler, DataHandler
from .post_processing import PostProcessingMixin


class PklHandler(PostProcessingMixin, DataHandler):
    """Handler for Python pickle format files.

    Supports fetching and storing data in pickle format with optional
    protocol configuration.
    """

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        """Initialize PklHandler.

        Args:
            protocol: Pickle protocol version to use (default: HIGHEST_PROTOCOL)
        """
        self.protocol = protocol

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
        """Fetch data from pickle file.

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

            with open(file_path, "rb") as f:
                data = pickle.load(f)

            if not isinstance(data, list):
                raise ValueError(
                    f"Pickle file must contain a list of objects, got {type(data).__name__}"
                )

            # Validate that all items are dictionaries
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"Pickle file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
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
        overwrite: bool = True,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to pickle file.

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
                with open(file_path, "rb") as f:
                    existing_data = pickle.load(f)
                if isinstance(existing_data, list):
                    data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, "wb") as f:
                pickle.dump(data_to_store, f, protocol=self.protocol)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0


class AsyncPklHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for Python pickle format files."""

    def __init__(self, protocol: int = 4):
        self.protocol = protocol

    async def fetch(self, path, table, cols=None, filter_=None, limit=None, strict=True, types=None):
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            def _load_pickle():
                with open(file_path, "rb") as f:
                    return pickle.load(f)

            data = await asyncio.to_thread(_load_pickle)

            if not isinstance(data, list):
                raise ValueError(f"Pickle file must contain a list of objects, got {type(data).__name__}")

            # Validate that all items are dictionaries
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"Pickle file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
                    )

            data = self._apply_processing(data, types, cols, filter_, limit)
            return data
        except Exception:
            if strict:
                raise
            return []

    async def store(self, data, path, table, cols=None, filter_=None, limit=None, overwrite=True, strict=True, types=None):
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            def _dump_pickle(data_to_process=data_to_store):
                # For append mode, read existing data and merge
                if not overwrite and file_path.exists():
                    with open(file_path, "rb") as f:
                        existing_data = pickle.load(f)
                    if isinstance(existing_data, list):
                        data_to_process = existing_data + data_to_process

                with open(file_path, "wb") as f:
                    pickle.dump(data_to_process, f, protocol=self.protocol)
                return len(data_to_process)

            return await asyncio.to_thread(_dump_pickle)
        except Exception:
            if strict:
                raise
            return 0
