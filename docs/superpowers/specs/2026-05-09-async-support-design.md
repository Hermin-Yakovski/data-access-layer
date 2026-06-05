# v0.2.0 Async Support Design

**Date:** 2026-05-09
**Status:** Approved
**Version:** 0.2.0

## Overview

Add async versions of `fetch()` and `store()` methods to all data handlers via separate `AsyncHandler` classes. This enables async/await usage while maintaining full backward compatibility.

**Goal:** Non-blocking I/O for concurrent operations without breaking existing sync code.

## API Design

Separate `AsyncHandler` classes with `Async` prefix, co-located in the same module as sync handlers:

```python
# dal/__init__.py exports
from dal import JsonHandler, AsyncJsonHandler
from dal import CsvHandler, AsyncCsvHandler
from dal import PklHandler, AsyncPklHandler
from dal import XlsxHandler, AsyncXlsxHandler
from dal import SqliteHandler, AsyncSqliteHandler
```

**Usage example:**
```python
# Sync (existing, unchanged)
handler = JsonHandler()
data = handler.fetch(path, "users.json")

# Async (new)
handler = AsyncJsonHandler()
data = await handler.fetch(path, "users.json")
```

**Type-safe by construction** — `AsyncJsonHandler().fetch()` returns an awaitable, while `JsonHandler().fetch()` returns data directly.

## Architecture

Separate parallel ABCs with shared post-processing logic:

```
DataHandler (ABC)
    ├─ JsonHandler
    ├─ CsvHandler
    ├─ PklHandler
    ├─ XlsxHandler
    └─ SqliteHandler

AsyncDataHandler (ABC)  ← New, parallel structure
    ├─ AsyncJsonHandler  ← New
    ├─ AsyncCsvHandler   ← New
    ├─ AsyncPklHandler   ← New
    ├─ AsyncXlsxHandler  ← New
    └─ AsyncSqliteHandler← New

PostProcessingMixin  ← Shared by both sync and async
```

### AsyncDataHandler ABC

```python
class AsyncDataHandler(ABC):
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
        """Fetch data asynchronously."""
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
        """Store data asynchronously."""
        pass
```

**Code sharing:** Both sync and async handlers use `PostProcessingMixin._apply_processing()` for type coercion, filtering, and limiting — only the I/O differs.

## Implementation Details

### Event Loop Handling

Handlers auto-detect the running event loop using `asyncio.get_running_loop()`. No explicit event loop management required by users.

### Dependencies

- `aiofiles` — async file I/O for JSON, CSV, Pickle, XLSX
- `aiosqlite` — async SQLite operations

### Example: AsyncJsonHandler

```python
import aiofiles
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from data_access_layer.abc import AsyncDataHandler
from data_access_layer.post_processing import PostProcessingMixin


class AsyncJsonHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for JSON format files."""

    def __init__(self, encoding: str = "utf-8", indent: int = 2):
        self.encoding = encoding
        self.indent = indent

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
        """Fetch data from JSON file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            # Async file I/O
            async with aiofiles.open(file_path, "r", encoding=self.encoding) as f:
                content = await f.read()
                data = json.loads(content)

            if not isinstance(data, list):
                raise ValueError(
                    f"JSON file must contain a list of objects, got {type(data).__name__}"
                )

            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSON file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
                    )

            # Shared post-processing
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
        """Store data to JSON file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            # Shared post-processing
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
```

**All handlers follow the same pattern:** Async I/O → validation → shared `_apply_processing()` → return.

### Handlers to Implement

1. `AsyncJsonHandler` — JSON files using `aiofiles`
2. `AsyncCsvHandler` — CSV files using `aiofiles`
3. `AsyncPklHandler` — Pickle files using `aiofiles` + `asyncio.to_thread` for pickle ops
4. `AsyncXlsxHandler` — Excel XLSX using `aiofiles` + `asyncio.to_thread` for openpyxl
5. `AsyncSqliteHandler` — SQLite using `aiosqlite`

## Dependencies

`openpyxl` becomes a default dependency. New async dependencies are optional:

```toml
[tool.poetry.dependencies]
python = "^3.8"
aiofiles = {version = "^23.0.0", optional = true}
aiosqlite = {version = "^0.19.0", optional = true}
openpyxl = "^24.0.0"  # Default, no longer optional

[tool.poetry.extras]
async = ["aiofiles", "aiosqlite"]
```

**Installation options:**
```bash
# Standard install (includes XLSX support)
pip install data-access-layer

# Add async support
pip install data-access-layer[async]

# Development with async
pip install -e ".[dev,async]"
```

## Testing

Focus on async-specific I/O behavior; trust shared `PostProcessingMixin`:

```python
# tests/unit/test_async_json_handler.py
import pytest

@pytest.mark.asyncio
async def test_async_json_file_io():
    """Test async file I/O operations."""
    handler = AsyncJsonHandler()
    # Create test file
    test_data = [{"name": "Alice", "age": 30}]
    await handler.store(test_data, Path("test_data"), "test.json")
    # Read back
    result = await handler.fetch(Path("test_data"), "test.json")
    assert result == test_data

@pytest.mark.asyncio
async def test_async_json_error_handling():
    """Test lenient mode returns empty list on error."""
    handler = AsyncJsonHandler()
    result = await handler.fetch(Path("nonexistent"), "missing.json", strict=False)
    assert result == []
```

**Test structure:** `tests/unit/test_async_*_handler.py` for each handler.

**No sync/async comparison tests** — `PostProcessingMixin` is already tested separately.

## Documentation

### README Updates

- New "Async Usage" section with examples
- Updated installation instructions with `[async]` extra
- Quick start examples for both sync and async

### Docstrings

All async methods get proper async documentation:

```python
async def fetch(self, ...) -> List[Dict[str, Any]]:
    """Fetch data asynchronously from JSON file.
    
    This method performs non-blocking I/O and is suitable for
    use in async/await contexts.
    
    Args:
        path: Directory containing the file
        table: Filename to fetch from
        ...
    
    Returns:
        List of row dictionaries
    
    Raises:
        FileNotFoundError: If path or file doesn't exist (when strict=True)
        ValueError: If file format is invalid (when strict=True)
        ...
    """
```

### Migration Guide

Brief section showing how to migrate from sync to async:

```python
# Before
handler = JsonHandler()
data = handler.fetch(path, table)

# After
handler = AsyncJsonHandler()
data = await handler.fetch(path, table)
```

## Error Handling

Lenient mode (`strict=False`) behaves identically to sync handlers:
- Returns empty list `[]` from `fetch()` on error
- Returns `0` from `store()` on error
- No logging or tracking by default
- Consistent behavior between sync and async

## Success Criteria

- [ ] All 5 async handlers implemented
- [ ] Async handlers pass all unit tests
- [ ] `PostProcessingMixin` shared logic verified working
- [ ] Documentation updated with async examples
- [ ] Installation via `[async]` extra works correctly
- [ ] Backward compatibility maintained (no breaking changes)
- [ ] Type hints pass mypy checks

## Timeline

v0.2.0 release with complete async parity across all handlers.