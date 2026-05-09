from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


class DataHandler(ABC):
    """Abstract base class for data access handlers.

    All handlers must implement fetch() and store() methods with consistent
    behavior for column selection, filtering, and limiting.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Handler-specific initialization options."""
        pass

    @abstractmethod
    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from the source.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable that receives a row dict, returns True to include
            limit: Maximum number of rows to return (applied AFTER filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries

        Raises:
            FileNotFoundError: If path or file doesn't exist (when strict=True)
            ValueError: If file format is invalid (when strict=True)
            PermissionError: If file cannot be read (when strict=True)
        """
        pass

    @abstractmethod
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
        """Store data to the source.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable that receives a row dict, returns True to include
            limit: Maximum number of rows to store (applied AFTER filtering)
            overwrite: If True, replace existing file; if False, append/merge
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored

        Raises:
            FileNotFoundError: If path doesn't exist (when strict=True)
            ValueError: If data format is invalid (when strict=True)
            PermissionError: If file cannot be written (when strict=True)
        """
        pass


class AsyncDataHandler(ABC):
    """Abstract base class for async data access handlers.

    All async handlers must implement async fetch() and store() methods
    with consistent behavior for column selection, filtering, and limiting.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Handler-specific initialization options."""
        pass

    @abstractmethod
    async def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from the source asynchronously.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable that receives a row dict, returns True to include
            limit: Maximum number of rows to return (applied AFTER filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries

        Raises:
            FileNotFoundError: If path or file doesn't exist (when strict=True)
            ValueError: If file format is invalid (when strict=True)
            PermissionError: If file cannot be read (when strict=True)
        """
        pass

    @abstractmethod
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
    ) -> int:
        """Store data to the source asynchronously.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable that receives a row dict, returns True to include
            limit: Maximum number of rows to store (applied AFTER filtering)
            overwrite: If True, replace existing file; if False, append/merge
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored

        Raises:
            FileNotFoundError: If path doesn't exist (when strict=True)
            ValueError: If data format is invalid (when strict=True)
            PermissionError: If file cannot be written (when strict=True)
        """
        pass
