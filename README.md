# data-access-layer

A unified Python data access layer providing a consistent interface for reading and writing data across multiple file formats (JSON, CSV, Pickle, Excel XLSX).

## Features

- **Consistent API**: Single interface (`fetch` and `store` methods) for all file formats
- **Data filtering**: Apply filters, column selection, and limits when reading/writing
- **Type coercion**: Automatic type conversion for int, float, str, and bool types
- **Error handling**: Configurable strict/lenient mode for error handling
- **Type hints**: Full type annotation support
- **Well-tested**: Comprehensive unit and integration tests
- **Flexible**: Support for multiple data formats with format-specific options

## Installation

### Using pip (from PyPI)

```bash
# Basic installation (JSON, CSV, Pickle, XLSX support)
pip install data-access-layer

# With async support
pip install data-access-layer[async]
```

### Using Poetry (for development)

```bash
# Install with Poetry
poetry add data-access-layer

# Install with Excel support
poetry add data-access-layer --extras xlsx
```

## Quick Start

```python
from pathlib import Path
from dal import JsonHandler, CsvHandler, PklHandler

# JSON
json_handler = JsonHandler()
data = json_handler.fetch(path=Path("data"), table="users.json")
json_handler.store(data, path=Path("output"), table="users.json")

# CSV
csv_handler = CsvHandler(delimiter=',', encoding='utf-8')
data = csv_handler.fetch(path=Path("data"), table="users.csv")
csv_handler.store(data, path=Path("output"), table="users.csv")

# Pickle
pkl_handler = PklHandler(protocol=4)
data = pkl_handler.fetch(path=Path("data"), table="users.pkl")
pkl_handler.store(data, path=Path("output"), table="users.pkl")
```

## Async Usage

All handlers have async versions that can be used with `async/await`:

```python
import asyncio
from pathlib import Path
from dal import AsyncJsonHandler, AsyncCsvHandler, AsyncSqliteHandler

async def main():
    # Async JSON
    json_handler = AsyncJsonHandler()
    data = await json_handler.fetch(path=Path("data"), table="users.json")

    # Async CSV
    csv_handler = AsyncCsvHandler()
    data = await csv_handler.fetch(path=Path("data"), table="users.csv")

    # Async SQLite
    sqlite_handler = AsyncSqliteHandler()
    data = await sqlite_handler.fetch(path=Path("data"), table="users")

asyncio.run(main())
```

**Available async handlers:**
- `AsyncJsonHandler`
- `AsyncCsvHandler`
- `AsyncPklHandler`
- `AsyncXlsxHandler`
- `AsyncSqliteHandler`

All async handlers support the same features as their sync counterparts:
- Type coercion
- Column selection
- Filtering
- Limiting
- Lenient mode

```python
handler = AsyncJsonHandler()
data = await handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'age': int, 'active': bool},  # Type coercion
    cols=["name", "age"],      # Column selection
    filter_=lambda row: row["age"] > 25,  # Filtering
    limit=10,                   # Limiting
    strict=False                # Lenient mode
)
```

## Handlers

### JsonHandler

For JSON format files.

```python
from dal import JsonHandler

handler = JsonHandler(encoding='utf-8', indent=2)
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'age': int, 'active': bool},  # Optional: type coercion
    cols=["name", "age"],      # Optional: column selection
    filter_=lambda row: row["age"] > 25,  # Optional: filter rows
    limit=10,                   # Optional: limit rows
    strict=True                 # Optional: raise exceptions (default)
)
```

### CsvHandler

For CSV format files.

```python
from dal import CsvHandler

handler = CsvHandler(delimiter=',', encoding='utf-8')
data = handler.fetch(
    path=Path("data"),
    table="users.csv",
    cols=["name", "age"],
    filter_=lambda row: int(row["age"]) > 25,
    limit=10
)
```

### PklHandler

For Python pickle format files.

```python
from dal import PklHandler

handler = PklHandler(protocol=4)  # pickle protocol version
data = handler.fetch(
    path=Path("data"),
    table="users.pkl",
    cols=["name", "age"],
    filter_=lambda row: row["age"] > 25,
    limit=10
)
```

### XlsxHandler

For Excel XLSX format files (requires `openpyxl`).

```python
from dal import XlsxHandler

handler = XlsxHandler(sheet_name='Sheet1', header_row=0)
data = handler.fetch(
    path=Path("data"),
    table="users.xlsx",
    cols=["name", "age"],
    filter_=lambda row: row["age"] > 25,
    limit=10
)
```

## Type Coercion

All handlers support automatic type coercion via the `types` parameter:

```python
from pathlib import Path
from dal import JsonHandler

handler = JsonHandler()

# Fetch with type coercion
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'id': int, 'age': int, 'active': bool}
)

# Type guarantees:
for row in data:
    user_id: int = row['id']      # Guaranteed to be int
    age: int = row['age']          # Guaranteed to be int
    active: bool = row['active']   # Guaranteed to be bool

# Store with type coercion
handler.store(
    data=new_users,
    path=Path("output"),
    table="users.json",
    types={'id': str, 'age': str}  # Convert to strings before storing
)
```

**Supported types:** `int`, `float`, `str`, `bool`

**Type coercion rules:**
- `None` values convert to defaults (0, 0.0, "", False)
- String conversions follow Python's built-in conversion rules
- Bool strings are case-insensitive ("true", "false", "1", "0")

## API Reference

### DataHandler (Abstract Base Class)

All handlers inherit from `DataHandler` and implement:

#### fetch()

Fetch data from a file.

```python
def fetch(
    path: Path,
    table: str,
    cols: Optional[Iterable[str]] = None,
    filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
    limit: Optional[int] = None,
    types: Optional[Dict[str, type]] = None,
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch data from file.

    Args:
        path: Directory containing the file
        table: Filename to fetch from
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to return (applied after filtering)
        types: Optional dict mapping column names to target types for coercion
        strict: If True, raise exceptions; if False, return empty list on error

    Returns:
        List of row dictionaries
    """
```

#### store()

Store data to a file.

```python
def store(
    data: List[Dict[str, Any]],
    path: Path,
    table: str,
    cols: Optional[Iterable[str]] = None,
    filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
    limit: Optional[int] = None,
    types: Optional[Dict[str, type]] = None,
    overwrite: bool = True,
    strict: bool = True,
) -> int:
    """Store data to file.

    Args:
        data: List of row dictionaries to store
        path: Directory containing the file
        table: Filename to store to
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to store (applied after filtering)
        types: Optional dict mapping column names to target types for coercion
        overwrite: If True, replace existing file; if False, append
        strict: If True, raise exceptions; if False, return 0 on error

    Returns:
        Number of rows stored
    """
```

## Data Processing Order

Operations are applied in the following order:

1. **Type coercion** (`types`): Convert values to specified types
2. **Column selection** (`cols`): Select specific columns
3. **Filtering** (`filter_`): Apply filter function to rows
4. **Limiting** (`limit`): Apply limit to filtered results

```python
# Example: Get name and age for users over 25, limit to 10 results
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'age': int},             # Step 1: Coerce types
    cols=["name", "age"],           # Step 2: Select columns
    filter_=lambda row: row["age"] > 25,  # Step 3: Filter rows
    limit=10                         # Step 4: Limit results
)
```

## Error Handling

### Strict Mode (default)

```python
handler = JsonHandler()
try:
    data = handler.fetch(path=Path("nonexistent"), table="data.json", strict=True)
except FileNotFoundError:
    print("File not found!")
```

### Lenient Mode

```python
handler = JsonHandler()
data = handler.fetch(path=Path("nonexistent"), table="data.json", strict=False)
# Returns empty list [] instead of raising exception
```

## Overwrite vs Append

### Overwrite (default)

```python
handler.store(
    data=[{"name": "Bob"}],
    path=Path("output"),
    table="users.json",
    overwrite=True  # Replace existing file
)
```

### Append

```python
handler.store(
    data=[{"name": "Bob"}],
    path=Path("output"),
    table="users.json",
    overwrite=False  # Append to existing file
)
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with coverage
pytest --cov=dal --cov-report=html
```

## Development

```bash
# Install with development dependencies
pip install -e ".[dev,xlsx]"

# Run tests
pytest

# Format code
black dal tests

# Type check
mypy dal
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
