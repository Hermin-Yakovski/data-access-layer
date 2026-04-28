# XlsxHandler API Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign XlsxHandler to treat `path` as file path and `table` as sheet name, aligning with the multi-table nature of Excel files.

**Architecture:** Remove `sheet_name` class attribute, use `path` directly as file path, use `table` as sheet name in `wb[table]` and `ws.title = table`. Keep `header_row` as class attribute.

**Tech Stack:** Python 3.11+, openpyxl, pytest

---

## File Structure

**Files to modify:**
1. `dal/xlsx_handler.py` - Remove `sheet_name`, update `fetch()` and `store()` to use path=file, table=sheet
2. `tests/integration/test_xlsx_handler.py` - Update all test calls to use new API
3. `tests/unit/test_xlsx_handler.py` - Update test calls to use new API

---

### Task 1: Update XlsxHandler.__init__ to remove sheet_name

**Files:**
- Modify: `dal/xlsx_handler.py:23-38`

- [ ] **Step 1: Read current implementation**

Read `dal/xlsx_handler.py` lines 1-40 to understand current structure.

- [ ] **Step 2: Write failing test for new API**

Create test file `tests/test_new_api.py` with a test that uses the new API:

```python
# tests/test_new_api.py
from pathlib import Path
import pytest

try:
    from dal import XlsxHandler
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
def test_xlsx_handler_init_without_sheet_name():
    """XlsxHandler should only take header_row parameter."""
    handler = XlsxHandler(header_row=0)
    assert hasattr(handler, 'header_row')
    assert not hasattr(handler, 'sheet_name')
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_new_api.py -v`
Expected: FAIL - XlsxHandler still requires sheet_name

- [ ] **Step 4: Update __init__ to remove sheet_name**

In `dal/xlsx_handler.py`, replace the `__init__` method (lines 23-38):

```python
def __init__(self, header_row: int = 0):
    """Initialize XlsxHandler.

    Args:
        header_row: Row number containing column headers (0-indexed, default: 0)

    Raises:
        ImportError: If openpyxl is not installed
    """
    if not HAS_OPENPYXL:
        raise ImportError(
            "openpyxl is required for XlsxHandler. Install it with: pip install openpyxl"
        )
    self.header_row = header_row
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_new_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dal/xlsx_handler.py tests/test_new_api.py
git commit -m "refactor: remove sheet_name from XlsxHandler.__init__"
```

---

### Task 2: Update XlsxHandler.fetch() to use path as file path

**Files:**
- Modify: `dal/xlsx_handler.py:40-118`
- Test: `tests/test_new_api.py`

- [ ] **Step 1: Write failing test for new fetch API**

Add to `tests/test_new_api.py`:

```python
@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
def test_fetch_new_api_with_real_file(tmp_path):
    """fetch() should use path as file path and table as sheet name."""
    from openpyxl import Workbook

    # Create test file with a sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "owners"
    ws.append(["name", "age"])
    ws.append(["Alice", 30])

    file_path = tmp_path / "project1.xlsx"
    wb.save(file_path)

    # Use new API: path=file, table=sheet
    handler = XlsxHandler()
    result = handler.fetch(path=file_path, table="owners")
    assert result == [{"name": "Alice", "age": 30}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_new_api.py::test_fetch_new_api_with_real_file -v`
Expected: FAIL - Current implementation treats path as directory

- [ ] **Step 3: Update fetch() to use path as file path**

In `dal/xlsx_handler.py`, replace the `fetch()` method implementation (lines 62-98 in the try block):

```python
try:
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' not found")

    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[table]

        # Get header row
        headers = None
        rows_data = []
        for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
            if row_idx == self.header_row:
                headers = [
                    str(cell) if cell is not None else f"col_{i}"
                    for i, cell in enumerate(row)
                ]
            elif row_idx > self.header_row:
                rows_data.append(row)

        if headers is None:
            raise ValueError(f"Header row {self.header_row} not found in sheet")

        # Convert rows to dictionaries
        data = []
        for row in rows_data:
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = row[i]
            data.append(row_dict)
    finally:
        wb.close()

    # Apply column selection
    if cols is not None:
        cols_set = set(cols)
        data = [{k: v for k, v in row.items() if k in cols_set} for row in data]

    # Apply filtering
    if filter_ is not None:
        data = [row for row in data if filter_(row)]

    # Apply limit (after filtering)
    if limit is not None:
        data = data[:limit]

    return data
```

- [ ] **Step 4: Update fetch() docstring**

Update the docstring in `fetch()` (lines 49-60):

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

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_new_api.py::test_fetch_new_api_with_real_file -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dal/xlsx_handler.py tests/test_new_api.py
git commit -m "refactor: update XlsxHandler.fetch() to use path as file path, table as sheet name"
```

---

### Task 3: Update XlsxHandler.store() to use path as file path

**Files:**
- Modify: `dal/xlsx_handler.py:120-197`
- Test: `tests/test_new_api.py`

- [ ] **Step 1: Write failing test for new store API**

Add to `tests/test_new_api.py`:

```python
@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
def test_store_new_api_with_real_file(tmp_path):
    """store() should use path as file path and table as sheet name."""
    from openpyxl import load_workbook

    test_data = [{"name": "Bob", "age": 25}]
    file_path = tmp_path / "project1.xlsx"

    # Use new API: path=file, table=sheet
    handler = XlsxHandler()
    result = handler.store(data=test_data, path=file_path, table="owners")
    assert result == 1

    # Verify the sheet was created
    wb = load_workbook(file_path)
    assert "owners" in wb.sheetnames
    ws = wb["owners"]
    assert ws["A1"].value == "name"
    assert ws["A2"].value == "Bob"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_new_api.py::test_store_new_api_with_real_file -v`
Expected: FAIL - Current implementation treats path as directory

- [ ] **Step 3: Update store() to use path as file path**

In `dal/xlsx_handler.py`, replace the `store()` method implementation (lines 146-192):

```python
try:
    file_path = path

    # Prepare data to store
    data_to_store = data.copy()

    # Apply column selection
    if cols is not None:
        cols_set = set(cols)
        data_to_store = [
            {k: v for k, v in row.items() if k in cols_set} for row in data_to_store
        ]

    # Apply filtering
    if filter_ is not None:
        data_to_store = [row for row in data_to_store if filter_(row)]

    # Apply limit (after filtering)
    if limit is not None:
        data_to_store = data_to_store[:limit]

    # For append mode, read existing data and merge
    if not overwrite and file_path.exists():
        existing_data = self.fetch(path=file_path, table=table, strict=True)
        data_to_store = existing_data + data_to_store

    # Create or load workbook and write data
    if file_path.exists():
        wb = load_workbook(file_path)
        # Remove sheet if it exists (for overwrite mode)
        if overwrite and table in wb.sheetnames:
            wb.remove(wb[table])
        # Check if sheet exists, if not create it
        if table not in wb.sheetnames:
            ws = wb.create_sheet(table)
        else:
            ws = wb[table]
        # Clear existing data for overwrite mode
        if overwrite:
            for row in ws.iter_rows():
                for cell in row:
                    cell.value = None
    else:
        wb = Workbook()
        ws = wb.active
        if ws.title != table:
            ws.title = table

    if data_to_store:
        # Write header
        headers = list(data_to_store[0].keys())
        ws.append(headers)

        # Write data rows
        for row in data_to_store:
            ws.append([row.get(h, "") for h in headers])

    # Save workbook
    wb.save(file_path)

    return len(data_to_store)
```

- [ ] **Step 4: Update store() docstring**

Update the docstring in `store()` (lines 131-144):

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

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_new_api.py::test_store_new_api_with_real_file -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dal/xlsx_handler.py tests/test_new_api.py
git commit -m "refactor: update XlsxHandler.store() to use path as file path, table as sheet name"
```

---

### Task 4: Update integration tests to use new API

**Files:**
- Modify: `tests/integration/test_xlsx_handler.py`

- [ ] **Step 1: Update test_fetch_from_real_xlsx_file**

In `tests/integration/test_xlsx_handler.py`, update lines 24-42:

```python
def test_fetch_from_real_xlsx_file(self, temp_dir):
    """Fetch data from an actual XLSX file."""
    from openpyxl import Workbook

    # Create test data file
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["name", "age"])
    ws.append(["Alice", 30])
    ws.append(["Bob", 25])

    test_file = temp_dir / "users.xlsx"
    wb.save(test_file)

    # Fetch and verify - using new API: path=file, table=sheet
    handler = XlsxHandler()
    result = handler.fetch(path=test_file, table="Sheet1")
    assert result == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
```

- [ ] **Step 2: Update test_fetch_empty_file**

In `tests/integration/test_xlsx_handler.py`, update lines 44-58:

```python
def test_fetch_empty_file(self, temp_dir):
    """Fetch from an XLSX file with header only."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["name", "age"])

    test_file = temp_dir / "empty.xlsx"
    wb.save(test_file)

    handler = XlsxHandler()
    result = handler.fetch(path=test_file, table="Sheet1")
    assert result == []
```

- [ ] **Step 3: Update test_fetch_with_custom_sheet_name**

In `tests/integration/test_xlsx_handler.py`, update lines 60-75:

```python
def test_fetch_with_custom_sheet_name(self, temp_dir):
    """Fetch XLSX file with custom sheet name."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "CustomSheet"
    ws.append(["name", "age"])
    ws.append(["Alice", 30])

    test_file = temp_dir / "data.xlsx"
    wb.save(test_file)

    handler = XlsxHandler()
    result = handler.fetch(path=test_file, table="CustomSheet")
    assert result == [{"name": "Alice", "age": 30}]
```

- [ ] **Step 4: Update all remaining fetch tests**

For tests 4-10 in `TestXlsxHandlerFetchIntegration`, update the pattern:
- Old: `handler.fetch(path=temp_dir, table="users.xlsx", ...)`
- New: `handler.fetch(path=temp_dir / "users.xlsx", table="Sheet1", ...)`

Update lines 77-198 accordingly:

```python
# Pattern for all fetch tests:
# handler = XlsxHandler()
# result = handler.fetch(path=temp_dir / "users.xlsx", table="Sheet1", ...)
```

Specific updates:
- Line 92: `result = handler.fetch(path=temp_dir / "users.xlsx", cols=["name", "age"], table="Sheet1")`
- Line 110: `result = handler.fetch(path=temp_dir / "users.xlsx", filter_=lambda row: row["age"] > 25, table="Sheet1")`
- Line 128: `result = handler.fetch(path=temp_dir / "users.xlsx", limit=1, table="Sheet1")`
- Line 149: `result = handler.fetch(path=temp_dir / "users.xlsx", filter_=lambda row: row["age"] >= 30, limit=1, table="Sheet1")`
- Line 168: `handler.fetch(path=temp_dir / "users.xlsx", header_row=5, table="Sheet1", strict=True)`
- Line 184: `handler.fetch(path=temp_dir / "users.xlsx", header_row=5, table="Sheet1", strict=False)`
- Line 192: `handler.fetch(path=temp_dir / "missing.xlsx", table="Sheet1", strict=True)`
- Line 197: `handler.fetch(path=temp_dir / "missing.xlsx", table="Sheet1", strict=False)`

- [ ] **Step 5: Update all store tests**

For tests in `TestXlsxHandlerStoreIntegration`, update the pattern:
- Old: `handler.store(data=..., path=temp_dir, table="users.xlsx")`
- New: `handler.store(data=..., path=temp_dir / "users.xlsx", table="Sheet1")`

Update lines 205-350 accordingly:

```python
# Pattern for all store tests:
# handler = XlsxHandler()
# handler.store(data=test_data, path=temp_dir / "users.xlsx", table="Sheet1")
```

Specific updates:
- Line 212-216: `handler.store(data=test_data, path=temp_dir / "users.xlsx", table="Sheet1")`
- Line 235: `handler.store(data=test_data, path=temp_dir / "users.xlsx", table="CustomSheet")`
- Line 257: `handler.store(data=new_data, path=temp_dir / "users.xlsx", table="Sheet1", overwrite=True)`
- Line 282: `handler.store(data=new_data, path=temp_dir / "users.xlsx", table="Sheet1", overwrite=False)`
- Line 299: `handler.store(data=test_data, path=temp_dir / "users.xlsx", cols=["name", "age"], table="Sheet1")`
- Line 320: `handler.store(data=test_data, path=temp_dir / "users.xlsx", filter_=lambda row: row["age"] > 25, table="Sheet1")`
- Line 341: `handler.store(data=test_data, path=temp_dir / "users.xlsx", limit=1, table="Sheet1")`

- [ ] **Step 6: Run integration tests**

Run: `pytest tests/integration/test_xlsx_handler.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add tests/integration/test_xlsx_handler.py
git commit -m "test: update integration tests to use new XlsxHandler API"
```

---

### Task 5: Update unit tests to use new API

**Files:**
- Modify: `tests/unit/test_xlsx_handler.py`

- [ ] **Step 1: Update test_fetch_returns_empty_list_when_strict_false**

In `tests/unit/test_xlsx_handler.py`, update lines 16-24:

```python
def test_fetch_returns_empty_list_when_strict_false_and_file_not_found(self):
    """When strict=False and file not found, return empty list."""
    handler = XlsxHandler()
    result = handler.fetch(
        path=Path("nonexistent/data.xlsx"),
        table="Sheet1",
        strict=False
    )
    assert result == []
```

- [ ] **Step 2: Update test_fetch_raises_file_not_found_when_strict_true**

In `tests/unit/test_xlsx_handler.py`, update lines 26-34:

```python
def test_fetch_raises_file_not_found_when_strict_true(self):
    """When strict=True and file not found, raise FileNotFoundError."""
    handler = XlsxHandler()
    with pytest.raises(FileNotFoundError):
        handler.fetch(
            path=Path("nonexistent/data.xlsx"),
            table="Sheet1",
            strict=True
        )
```

- [ ] **Step 3: Update test_store_returns_zero_when_strict_false**

In `tests/unit/test_xlsx_handler.py`, update lines 43-52:

```python
def test_store_returns_zero_when_strict_false_and_path_not_found(self):
    """When strict=False and path doesn't exist, return 0."""
    handler = XlsxHandler()
    result = handler.store(
        data=[{"name": "Alice"}],
        path=Path("nonexistent/output.xlsx"),
        table="Sheet1",
        strict=False
    )
    assert result == 0
```

- [ ] **Step 4: Update test_store_raises_file_not_found_when_strict_true**

In `tests/unit/test_xlsx_handler.py`, update lines 54-63:

```python
def test_store_raises_file_not_found_when_strict_true(self):
    """When strict=True and path doesn't exist, raise FileNotFoundError."""
    handler = XlsxHandler()
    with pytest.raises(FileNotFoundError):
        handler.store(
            data=[{"name": "Alice"}],
            path=Path("nonexistent/output.xlsx"),
            table="Sheet1",
            strict=True
        )
```

- [ ] **Step 5: Run unit tests**

Run: `pytest tests/unit/test_xlsx_handler.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_xlsx_handler.py
git commit -m "test: update unit tests to use new XlsxHandler API"
```

---

### Task 6: Run all tests and verify

**Files:**
- All files

- [ ] **Step 1: Run complete test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All PASS

- [ ] **Step 2: Run with coverage**

Run: `pytest tests/ --cov=dal/xlsx_handler --cov-report=term-missing`
Expected: Coverage report shows no regressions

- [ ] **Step 3: Remove temporary test file**

Run: `rm tests/test_new_api.py`

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "test: complete XlsxHandler API redesign, all tests passing"
```

---

### Task 7: Update docstring in XlsxHandler class

**Files:**
- Modify: `dal/xlsx_handler.py:14-21`

- [ ] **Step 1: Update class docstring**

In `dal/xlsx_handler.py`, update lines 14-21:

```python
class XlsxHandler(DataHandler):
    """Handler for Excel XLSX format files.

    Supports fetching and storing data in XLSX format with support for
    multiple sheets in a single file. The sheet name is specified via
    the 'table' parameter in fetch() and store() methods.

    Requires openpyxl to be installed. If not available, imports will fail.
    """
```

- [ ] **Step 2: Commit**

```bash
git add dal/xlsx_handler.py
git commit -m "docs: update XlsxHandler class docstring for new API"
```
