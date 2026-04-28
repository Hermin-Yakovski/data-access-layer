# SqliteHandler Design

**Date:** 2026-04-28
**Status:** Approved

## Overview

Add SqliteHandler to the data-access-layer package, providing SQLite database support with the same fetch/store interface as other handlers. Unlike JSON/CSV/PKL handlers (single file = single dataset), SqliteHandler follows XlsxHandler's multi-table pattern: one database file contains multiple tables.

**Reference:** XlsxHandler (both deal with multiple tables in a single file)

---

## Architecture

### Handler Pattern Difference

**XlsxHandler:** `path` and `table` both passed to `fetch()`/`store()`
```python
handler = XlsxHandler(header_row=0)
handler.fetch(path=Path("data.xlsx"), table="Sheet1")
```

**SqliteHandler:** `path` set in `__init__`, only `table` passed to methods
```python
handler = SqliteHandler(path=Path("data.db"))
handler.fetch(table="users")
```

**Why the difference:** SQLite workflows typically work with one database at a time. Setting the path once reduces repetition.

---

## API

### `__init__(self, path: Path)`

Initialize handler with database file path.

```python
def __init__(self, path: Path):
    """Initialize SqliteHandler.

    Args:
        path: Path to the SQLite database file

    Raises:
        ImportError: Never (sqlite3 is stdlib)
    """
    self.path = path
```

**No other parameters:** SQLite has built-in schema/metadata, no configuration needed.

### `fetch(self, table, cols=None, filter_=None, limit=None, strict=True)`

Fetch data from a table.

```python
def fetch(
    self,
    table: str,
    cols: Optional[Iterable[str]] = None,
    filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
    limit: Optional[int] = None,
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch data from SQLite table.

    Args:
        table: Table name to fetch from
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to return (applied after filtering)
        strict: If True, raise exceptions; if False, return empty list on error

    Returns:
        List of row dictionaries

    Raises:
        FileNotFoundError: If database file doesn't exist (strict=True)
        OperationalError: If table doesn't exist (strict=True)
    """
```

### `store(self, data, table, cols=None, filter_=None, limit=None, overwrite=True, strict=True)`

Store data to a table (table must already exist).

```python
def store(
    self,
    data: List[Dict[str, Any]],
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
        table: Table name to store to (must exist)
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to store (applied after filtering)
        overwrite: If True, DELETE existing rows; if False, append
        strict: If True, raise exceptions; if False, return 0 on error

    Returns:
        Number of rows stored

    Raises:
        FileNotFoundError: If database file doesn't exist (strict=True)
        OperationalError: If table doesn't exist (strict=True)
    """
```

---

## Data Flow

### Fetch Operation
1. Open connection to `self.path`
2. Check if table exists
3. Execute `SELECT * FROM table`
4. Convert rows to list of dicts
5. Apply column selection (`cols` allowlist)
6. Apply row filtering (`filter_` callable)
7. Apply limit (to filtered results)
8. Close connection
9. Return list of dictionaries

### Store Operation
1. Open connection to `self.path`
2. Check if table exists (must exist — user creates schema)
3. Apply column selection (`cols` allowlist)
4. Apply row filtering (`filter_` callable)
5. Apply limit (to filtered results)
6. If `overwrite=True`: `DELETE FROM table`
7. Insert rows (only existing columns, NULL for missing)
8. Commit transaction
9. Close connection
10. Return number of rows inserted

**Why filter/limit in Python:** Consistency with other handlers. The callable-based filtering works the same way across all handlers.

---

## Behavior

### Table Creation
**Table must exist before storing.** SqliteHandler does NOT create tables. Users must create schema separately:

```python
# User creates table first
import sqlite3
conn = sqlite3.connect("data.db")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
conn.commit()
conn.close()

# Then use SqliteHandler
handler = SqliteHandler(path=Path("data.db"))
handler.store([{"name": "Alice", "age": 30}], table="users")
```

### Column Matching
- **Extra columns in data:** Silently ignored (only insert columns that exist in table)
- **Missing columns in data:** NULL inserted for missing columns
- **No error on column mismatch:** By design, permissive insertion

### Overwrite Mode
- `overwrite=True`: `DELETE FROM table` before inserting (clears all rows, keeps schema)
- `overwrite=False`: Append to existing rows (no DELETE)

### Transactions
- Per-operation: Each fetch/store opens connection, executes, closes (auto-commit)
- No cross-operation transactions (use raw sqlite3 for complex transactions)

---

## Error Handling

### Strict Mode (`strict=True`, default)
| Error Type | When | Message |
|------------|------|---------|
| `FileNotFoundError` | Database file doesn't exist | `"Database file '{path}' does not exist"` |
| `OperationalError` (wrapped) | Table doesn't exist | `"Table '{table}' does not exist in database '{path}'"` |
| `IntegrityError` | Constraint violation (PK, NOT NULL, FK) | Propagates as-is |
| `ValueError` | Data format issues | Context-specific message |

### Lenient Mode (`strict=False`)
- All errors caught and return `[]` (fetch) or `0` (store)
- No logging or suppression indication

---

## Edge Cases

### Database States
1. **Database doesn't exist:** FileNotFoundError (strict) / `[]` (lenient)
2. **Table doesn't exist:** OperationalError wrapped (strict) / `[]` (lenient)
3. **Empty table:** Fetch returns `[]`
4. **Append to empty table:** `overwrite=False` with no data = just inserts
5. **Overwrite empty table:** `overwrite=True` with no data = DELETE (no-op), then inserts

### Data/Schema Mismatches
6. **Extra columns in data:** Silently ignored
7. **Missing columns in data:** NULL inserted
8. **Data has no rows:** Store returns `0`

### Type Handling
9. **None values:** Stored as NULL, fetched as None
10. **DateTime objects:** Stored as TIMESTAMP, fetched as datetime (sqlite3 default)
11. **Boolean values:** Stored as INTEGER (0/1), fetched as int (not bool)
12. **Large integers:** SQLite arbitrary precision, fetched as int

### Multi-Database Workflows
13. **Different databases:** Create new handler instance (path is immutable)
14. **In-memory database:** `path=Path(":memory:")` works for testing

### Concurrency
15. **Database locked:** Another process has write lock — OperationalError (strict) / retry (lenient)
16. **Primary key conflicts:** IntegrityError (user must handle)
17. **NOT NULL violations:** IntegrityError (user must ensure complete data)

### Performance
18. **Large result sets:** All rows loaded into memory (not streaming)
19. **Large inserts:** Single transaction, could hit limits for very large datasets
20. **Filter performance:** Applied in Python, not SQL WHERE (use raw sqlite3 for performance)

---

## Package Integration

### Files Created
- `dal/sqlite_handler.py` — New handler implementation

### Files Modified
- `dal/__init__.py` — Add SqliteHandler to exports

```python
# dal/__init__.py
from .abc import DataHandler
from .json_handler import JsonHandler
from .csv_handler import CsvHandler
from .pkl_handler import PklHandler
from .sqlite_handler import SqliteHandler  # NEW

try:
    from .xlsx_handler import XlsxHandler
    _xlsx_available = True
except ImportError:
    _xlsx_available = False

if _xlsx_available:
    __all__ = ["DataHandler", "JsonHandler", "CsvHandler", "PklHandler", "SqliteHandler", "XlsxHandler"]
else:
    __all__ = ["DataHandler", "JsonHandler", "CsvHandler", "PklHandler", "SqliteHandler"]
```

### Dependencies
No changes — `sqlite3` is Python stdlib.

---

## Usage Examples

```python
from pathlib import Path
from dal import SqliteHandler

# Basic fetch
handler = SqliteHandler(path=Path("data.db"))
users = handler.fetch(table="users")

# Fetch with filter and limit
adults = handler.fetch(
    table="users",
    filter_=lambda row: row["age"] >= 18,
    limit=100
)

# Fetch with column selection
names = handler.fetch(table="users", cols=["name", "email"])

# Store with overwrite (replace table contents)
handler.store(
    data=[{"name": "Alice", "age": 30}],
    table="users",
    overwrite=True
)

# Store with append mode
handler.store(
    data=[{"name": "Bob", "age": 25}],
    table="users",
    overwrite=False
)

# Lenient error handling
missing = handler.fetch(table="nonexistent", strict=False)  # Returns []
```

---

## Testing Strategy

### Unit Tests (`tests/unit/test_sqlite_handler.py`)
- `__init__` behavior (stores path attribute)
- Import handling (sqlite3 is stdlib, always available)
- Filter logic, column selection, limit application

### Integration Tests (`tests/integration/test_sqlite_handler.py`)
- Create temp databases with pytest fixtures
- Fetch from real tables
- Store to real tables (with pre-created schema)
- Overwrite mode behavior (DELETE then INSERT)
- Column matching (extra ignored, missing = NULL)
- Error conditions (file not found, table not found)
- Filter, cols, limit parameters
- Empty tables, empty data

**Key difference from XlsxHandler:** No optional dependency handling (sqlite3 is stdlib).
