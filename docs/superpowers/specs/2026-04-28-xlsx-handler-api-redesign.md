# XlsxHandler API Redesign

**Goal:** Align XlsxHandler's API with the multi-table nature of Excel files by treating `path` as the file path and `table` as the sheet name.

**Architecture:** Single handler instance can work with multiple sheets in the same file by specifying different `table` values per call.

**Tech Stack:** Python 3.11+, openpyxl, existing test infrastructure (pytest)

---

## Current Behavior

```python
handler = XlsxHandler(sheet_name="Sheet1", header_row=0)
# path = directory
# table = filename
handler.fetch(path=Path("data"), table="users.xlsx")
```

## New Behavior

```python
handler = XlsxHandler(header_row=0)
# path = full file path
# table = sheet name
handler.fetch(path=Path("data/users.xlsx"), table="owners")
```

---

## Changes to XlsxHandler

### `__init__` Method

**Remove:**
- `sheet_name` parameter and attribute

**Keep:**
- `header_row` parameter (class-level configuration for all operations)

```python
def __init__(self, header_row: int = 0):
    """Initialize XlsxHandler.

    Args:
        header_row: Row number containing column headers (0-indexed, default: 0)
    """
    if not HAS_OPENPYXL:
        raise ImportError(
            "openpyxl is required for XlsxHandler. Install it with: pip install openpyxl"
        )
    self.header_row = header_row
```

### `fetch()` Method

**Changes:**
- `path` is now the full file path (use directly, no longer combine with `table`)
- `table` is now the sheet name (`ws = wb[table]`)
- Remove directory existence check
- Check if file exists at `path` directly

```python
def fetch(
    self,
    path: Path,
    table: str,
    cols: Optional[Iterable[str]] = None,
    filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
    limit: Optional[int] = None,
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch data from XLSX file sheet.

    Args:
        path: Full path to the XLSX file
        table: Sheet name to fetch from
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to return (applied after filtering)
        strict: If True, raise exceptions; if False, return empty list on error

    Returns:
        List of row dictionaries
    """
```

**Implementation changes:**
```python
# Old:
if not path.exists():
    raise FileNotFoundError(f"Directory '{path}' does not exist")
file_path = path / table
ws = wb[self.sheet_name]

# New:
if not path.exists():
    raise FileNotFoundError(f"File '{path}' not found")
ws = wb[table]
```

### `store()` Method

**Changes:**
- `path` is now the full file path
- `table` is now the sheet name (`ws.title = table`)
- For append mode: read from same file, same sheet

```python
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
    """Store data to XLSX file sheet.

    Args:
        data: List of row dictionaries to store
        path: Full path to the XLSX file
        table: Sheet name to store to
        cols: Columns to include (allowlist, None = all columns)
        filter_: Optional callable for row filtering
        limit: Maximum rows to store (applied after filtering)
        overwrite: If True, replace sheet; if False, append to sheet
        strict: If True, raise exceptions; if False, return 0 on error

    Returns:
        Number of rows stored
    """
```

**Implementation changes:**
```python
# Old:
file_path = path / table
ws.title = self.sheet_name

# New:
file_path = path
ws.title = table
```

**For append mode:**
```python
# Old:
existing_data = self.fetch(path=path, table=table, strict=True)

# New:
existing_data = self.fetch(path=path, table=table, strict=True)
# Same call, but now table is sheet name
```

---

## Test Changes

### Integration Tests (`tests/integration/test_xlsx_handler.py`)

**Old pattern:**
```python
handler = XlsxHandler(sheet_name="CustomSheet")
result = handler.fetch(path=temp_dir, table="data.xlsx")
```

**New pattern:**
```python
handler = XlsxHandler()
result = handler.fetch(path=temp_dir / "data.xlsx", table="CustomSheet")
```

**Specific test updates:**
1. `test_fetch_from_real_xlsx_file` - Use `path=temp_dir / "users.xlsx"`, `table="Sheet1"`
2. `test_fetch_with_custom_sheet_name` - Remove `sheet_name` param, pass as `table`
3. `test_store_with_custom_sheet_name` - Same pattern
4. All other tests - Combine directory and filename into `path`, use sheet name for `table`

### Unit Tests

Update unit tests similarly to match new API pattern.

---

## Error Handling

**FileNotFoundError:**
- Old: "Directory '{path}' does not exist" or "File '{file_path}' not found"
- New: "File '{path}' not found"

**KeyError (invalid sheet name):**
- Propagates from openpyxl when accessing non-existent sheet
- Caught by general exception handler for lenient mode

---

## Edge Cases

1. **File doesn't exist:** FileNotFoundError in strict mode, empty list/0 in lenient mode
2. **Sheet doesn't exist:** KeyError from openpyxl, propagates in strict mode, empty list/0 in lenient mode
3. **Multiple sheets in file:** Each sheet accessed via different `table` value
4. **Append mode (`overwrite=False`) to existing sheet:** Reads existing data from that sheet and appends
5. **Append mode (`overwrite=False`) to non-existent sheet:** KeyError (sheet must exist for append mode)
6. **Overwrite to non-existent file:** Creates new file with specified sheet
