# Data Access Layer Design

**Date:** 2026-04-27
**Author:** Brainstorming session
**Status:** Approved

## Overview

A general-purpose Python package for data access, providing specific handlers that implement an abstract `DataHandler` interface. The package targets data analysis workflows where analysts need to load datasets from various sources, transform them, and save results.

**Target use case:** Data analysis workflow with small-to-medium datasets (MBs to a few GBs) that fit in memory.

## Package Structure

```
data-access-layer/
├── dal/
│   ├── __init__.py          # Package exports
│   ├── abc.py               # DataHandler abstract base class
│   ├── json_handler.py      # JsonHandler implementation
│   ├── csv_handler.py       # CsvHandler implementation
│   ├── xlsx_handler.py      # XlsxHandler implementation
│   └── pkl_handler.py       # PklHandler implementation
├── tests/
│   ├── unit/                # Unit tests with mocks
│   └── integration/         # Integration tests with real files
├── pyproject.toml           # Package config
├── README.md
└── LICENSE
```

## Abstract Base Class

All handlers implement the `DataHandler` abstract base class:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, List, Dict


class DataHandler(ABC):
    """Abstract base class for data access handlers."""

    def __init__(self, **kwargs):
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
            cols: Columns to include (allowlist, None = all)
            filter_: Callable that receives a row dict, return True to include
            limit: Maximum number of rows to return (applied AFTER filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries
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
            cols: Columns to include (allowlist, None = all)
            filter_: Callable that receives a row dict, return True to include
            limit: Maximum number of rows to store (applied AFTER filtering)
            overwrite: If True, replace file; if False, append/merge
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored
        """
        pass
```

## Handler Implementations

### JsonHandler

Handles .json formatted files.

```python
class JsonHandler(DataHandler):
    def __init__(self, encoding: str = 'utf-8', indent: int = 2):
        self.encoding = encoding
        self.indent = indent
```

- **Dependencies:** Python stdlib (`json`)
- **Default overwrite:** True

### CsvHandler

Handles .csv files.

```python
class CsvHandler(DataHandler):
    def __init__(self, delimiter: str = ',', encoding: str = 'utf-8'):
        self.delimiter = delimiter
        self.encoding = encoding
```

- **Dependencies:** Python stdlib (`csv`)
- **Default overwrite:** True

### XlsxHandler

Handles .xlsx files.

```python
class XlsxHandler(DataHandler):
    def __init__(self, sheet_name: str = 'Sheet1', header_row: int = 0):
        self.sheet_name = sheet_name
        self.header_row = header_row
```

- **Dependencies:** `openpyxl>=3.0.0` (optional)
- **Default overwrite:** True

### PklHandler

Handles binary .pkl files.

```python
class PklHandler(DataHandler):
    def __init__(self, protocol: int = 4):
        self.protocol = protocol
```

- **Dependencies:** Python stdlib (`pickle`)
- **Default overwrite:** True

## Data Flow

### Fetch Operation
1. Read file from `path/table`
2. Parse format-specific content
3. Apply column selection (`cols` allowlist)
4. Apply row filtering (`filter_` callable)
5. Apply limit (to filtered results)
6. Return list of dictionaries

### Store Operation
1. Apply column selection (`cols` allowlist)
2. Apply row filtering (`filter_` callable)
3. Apply limit (to filtered results)
4. Write to `path/table`
5. Return number of rows stored

## Error Handling

Errors are controlled by the `strict` parameter:

| Mode | Behavior |
|------|----------|
| `strict=True` (default) | Raises descriptive exceptions |
| `strict=False` | Returns empty results (0 for store, [] for fetch) |

**Common exception types:**
- `FileNotFoundError` - path or file doesn't exist
- `ValueError` - invalid format, encoding issues
- `PermissionError` - can't write to location

## Dependencies

### Core Installation
```bash
pip install data-access-layer
```
Includes: JSON, CSV, PKL handlers (stdlib only)

### Optional Extras
```bash
pip install data-access-layer[xlsx]  # Add XLSX support
pip install data-access-layer[all]   # Everything
```

| Handler | Dependencies |
|---------|--------------|
| JsonHandler | stdlib (`json`) |
| CsvHandler | stdlib (`csv`) |
| PklHandler | stdlib (`pickle`) |
| XlsxHandler | `openpyxl>=3.0.0` (optional) |

## Testing Strategy

### Unit Tests (`tests/unit/`)
Test handler logic in isolation with mocked file operations:
- Filter logic with various callables
- Column selection behavior
- Limit application (after filtering)
- Error conditions

### Integration Tests (`tests/integration/`)
Test with real files:
- Actual file I/O operations
- Format-specific behavior
- Cross-handler consistency

## Package Exports

```python
# dal/__init__.py
from .abc import DataHandler
from .json_handler import JsonHandler
from .csv_handler import CsvHandler
from .pkl_handler import PklHandler

try:
    from .xlsx_handler import XlsxHandler
except ImportError:
    XlsxHandler = None  # Not installed

__all__ = ["DataHandler", "JsonHandler", "CsvHandler", "PklHandler", "XlsxHandler"]
```

## Usage Examples

```python
from pathlib import Path
from dal import JsonHandler

# Fetch with filter and limit
handler = JsonHandler()
users = handler.fetch(
    path=Path("data"),
    table="users.json",
    filter_=lambda row: row["age"] > 25,
    limit=10
)

# Store with column selection
handler.store(
    users,
    path=Path("output"),
    table="filtered_users.json",
    cols=["name", "email"],
    overwrite=True
)

# Lenient error handling
data = handler.fetch(
    path=Path("maybe_exists"),
    table="data.json",
    strict=False  # Returns [] instead of raising
)
```

## Implementation Notes

- File extensions are inferred from the `table` parameter
- `path` and `table` are separate parameters for clarity
- Filter function receives unpacked row as `**row` (dict)
- All handlers default to `overwrite=True` for consistency
- Design emphasizes simplicity over abstraction - each handler is self-contained