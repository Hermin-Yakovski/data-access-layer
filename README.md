# data-access-layer

A unified Python data access layer providing a consistent interface for reading and writing data across multiple file formats (JSON, CSV, Pickle, Excel XLSX).

## Features

- **Consistent API**: Single interface (`fetch` and `store` methods) for all file formats
- **Data filtering**: Apply filters, column selection, and limits when reading/writing
- **Error handling**: Configurable strict/lenient mode for error handling
- **Type hints**: Full type annotation support
- **Well-tested**: Comprehensive unit and integration tests
- **Flexible**: Support for multiple data formats with format-specific options

## Installation

```bash
# Basic installation (JSON, CSV, Pickle support)
pip install data-access-layer

# With Excel support
pip install data-access-layer[xlsx]
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

## Handlers

### JsonHandler

For JSON format files.

```python
from dal import JsonHandler

handler = JsonHandler(encoding='utf-8', indent=2)
data = handler.fetch(
    path=Path("data"),
    table="users.json",
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
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch data from file.

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
        overwrite: If True, replace existing file; if False, append
        strict: If True, raise exceptions; if False, return 0 on error

    Returns:
        Number of rows stored
    """
```

## Data Processing Order

Operations are applied in the following order:

1. **Column selection** (`cols`): Select specific columns
2. **Filtering** (`filter_`): Apply filter function to rows
3. **Limiting** (`limit`): Apply limit to filtered results

```python
# Example: Get name and age for users over 25, limit to 10 results
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    cols=["name", "age"],           # Step 1: Select columns
    filter_=lambda row: row["age"] > 25,  # Step 2: Filter rows
    limit=10                         # Step 3: Limit results
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
