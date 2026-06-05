# Async Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add async versions of `fetch()` and `store()` methods to all data handlers via separate `AsyncHandler` classes for non-blocking I/O operations.

**Architecture:** Separate parallel `AsyncDataHandler` ABC with `AsyncHandler` classes that share `PostProcessingMixin` logic but use async I/O (`aiofiles` for files, `aiosqlite` for SQLite). Event loop auto-detection via `asyncio.get_running_loop()`.

**Tech Stack:** Python 3.8+, `aiofiles` ^23.0.0, `aiosqlite` ^0.19.0, `pytest-asyncio` for testing

---

## File Structure

```
dal/
├── abc.py                    # Add AsyncDataHandler ABC
├── __init__.py               # Export AsyncHandler classes
├── json_handler.py           # Add AsyncJsonHandler
├── csv_handler.py            # Add AsyncCsvHandler
├── pkl_handler.py            # Add AsyncPklHandler
├── xlsx_handler.py           # Add AsyncXlsxHandler
├── sqlite_handler.py         # Add AsyncSqliteHandler
└── post_processing.py        # No changes (shared by both sync/async)

tests/unit/
├── test_async_json_handler.py      # New
├── test_async_csv_handler.py       # New
├── test_async_pkl_handler.py       # New
├── test_async_xlsx_handler.py      # New
└── test_async_sqlite_handler.py    # New

pyproject.toml               # Add aiofiles, aiosqlite, pytest-asyncio
```

---

### Task 1: Update pyproject.toml with async dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add async dependencies**

Add `aiofiles`, `aiosqlite` as optional dependencies and `pytest-asyncio` as dev dependency:

```toml
[tool.poetry.dependencies]
python = "^3.8"
aiofiles = {version = "^23.0.0", optional = true}
aiosqlite = {version = "^0.19.0", optional = true}
openpyxl = "^24.0.0"

[tool.poetry.extras]
async = ["aiofiles", "aiosqlite"]

[tool.poetry.group.dev.dependencies]
pytest-asyncio = "^0.23.0"
```

- [ ] **Step 2: Install dependencies**

Run: `poetry install --extras async`

Expected: Dependencies installed successfully

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add async dependencies (aiofiles, aiosqlite, pytest-asyncio)"
```

---

### Task 2: Add AsyncDataHandler ABC

**Files:**
- Modify: `dal/abc.py`

- [ ] **Step 1: Write test for AsyncDataHandler ABC**

Create: `tests/unit/test_async_abc.py`

```python
import pytest
from data_access_layer.abc import AsyncDataHandler

def test_async_data_handler_is_abstract():
    """AsyncDataHandler should be an abstract class."""
    with pytest.raises(TypeError):
        AsyncDataHandler()

@pytest.mark.asyncio
async def test_async_data_handler_requires_fetch():
    """Subclass must implement async fetch."""
    class IncompleteHandler(AsyncDataHandler):
        async def store(self, data, path, table, **kwargs):
            return 0
    
    handler = IncompleteHandler()
    with pytest.raises(TypeError):
        await handler.fetch(None, "test")

@pytest.mark.asyncio
async def test_async_data_handler_requires_store():
    """Subclass must implement async store."""
    class IncompleteHandler(AsyncDataHandler):
        async def fetch(self, path, table, **kwargs):
            return []
    
    handler = IncompleteHandler()
    with pytest.raises(TypeError):
        await handler.store([], None, "test")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_async_abc.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncDataHandler'`

- [ ] **Step 3: Add AsyncDataHandler ABC to dal/abc.py**

Add to `dal/abc.py`:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


class DataHandler(ABC):
    # ... existing DataHandler code ...
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_abc.py -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add dal/abc.py tests/unit/test_async_abc.py
git commit -m "feat: add AsyncDataHandler abstract base class"
```

---

### Task 3: Implement AsyncJsonHandler

**Files:**
- Modify: `dal/json_handler.py`
- Create: `tests/unit/test_async_json_handler.py`

- [ ] **Step 1: Write failing test for AsyncJsonHandler.fetch()**

Create: `tests/unit/test_async_json_handler.py`

```python
import pytest
from pathlib import Path
from data_access_layer.json_handler import AsyncJsonHandler

@pytest.mark.asyncio
async def test_async_json_fetch_basic(tmp_path):
    """Test basic async fetch from JSON file."""
    # Create test data
    import json
    test_file = tmp_path / "test.json"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_text(json.dumps(test_data))

    # Fetch using async handler
    handler = AsyncJsonHandler()
    result = await handler.fetch(tmp_path, "test.json")

    assert result == test_data

@pytest.mark.asyncio
async def test_async_json_fetch_with_filter(tmp_path):
    """Test async fetch with filter."""
    import json
    test_file = tmp_path / "test.json"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_text(json.dumps(test_data))

    handler = AsyncJsonHandler()
    result = await handler.fetch(
        tmp_path, "test.json",
        filter_=lambda row: row["age"] > 25
    )

    assert len(result) == 1
    assert result[0]["name"] == "Alice"

@pytest.mark.asyncio
async def test_async_json_fetch_strict_false_missing_file(tmp_path):
    """Test lenient mode returns empty list for missing file."""
    handler = AsyncJsonHandler()
    result = await handler.fetch(tmp_path, "missing.json", strict=False)

    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_async_json_handler.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncJsonHandler'`

- [ ] **Step 3: Implement AsyncJsonHandler in dal/json_handler.py**

Add to `dal/json_handler.py` (after `JsonHandler` class):

```python
import aiofiles
import asyncio
import json
# ... existing imports ...

# ... existing JsonHandler class ...

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_json_handler.py -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Add tests for store() and run**

Add to `tests/unit/test_async_json_handler.py`:

```python
@pytest.mark.asyncio
async def test_async_json_store_basic(tmp_path):
    """Test basic async store to JSON file."""
    handler = AsyncJsonHandler()
    test_data = [{"name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, tmp_path, "output.json")

    assert rows_written == 1

    # Verify file content
    import json
    result_file = tmp_path / "output.json"
    result = json.loads(result_file.read_text())
    assert result == test_data

@pytest.mark.asyncio
async def test_async_json_store_append(tmp_path):
    """Test append mode."""
    import json
    handler = AsyncJsonHandler()

    # First write
    await handler.store([{"name": "A"}], tmp_path, "append.json")

    # Append
    await handler.store([{"name": "B"}], tmp_path, "append.json", overwrite=False)

    # Verify
    result_file = tmp_path / "append.json"
    result = json.loads(result_file.read_text())
    assert len(result) == 2
```

Run: `pytest tests/unit/test_async_json_handler.py -v`

Expected: PASS (5 tests)

- [ ] **Step 6: Update dal/__init__.py to export AsyncJsonHandler**

Add to `dal/__init__.py`:

```python
from .json_handler import JsonHandler, AsyncJsonHandler
```

- [ ] **Step 7: Commit**

```bash
git add dal/json_handler.py dal/__init__.py tests/unit/test_async_json_handler.py
git commit -m "feat: implement AsyncJsonHandler with async file I/O"
```

---

### Task 4: Implement AsyncCsvHandler

**Files:**
- Modify: `dal/csv_handler.py`
- Create: `tests/unit/test_async_csv_handler.py`

- [ ] **Step 1: Write failing test for AsyncCsvHandler**

Create: `tests/unit/test_async_csv_handler.py`

```python
import pytest
from pathlib import Path
from data_access_layer.csv_handler import AsyncCsvHandler

@pytest.mark.asyncio
async def test_async_csv_fetch_basic(tmp_path):
    """Test basic async fetch from CSV file."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,age\nAlice,30\nBob,25\n")

    handler = AsyncCsvHandler()
    result = await handler.fetch(tmp_path, "test.csv")

    assert len(result) == 2
    assert result[0] == {"name": "Alice", "age": "30"}
    assert result[1] == {"name": "Bob", "age": "25"}

@pytest.mark.asyncio
async def test_async_csv_store_basic(tmp_path):
    """Test basic async store to CSV file."""
    handler = AsyncCsvHandler()
    test_data = [{"name": "Charlie", "age": "35"}]
    rows_written = await handler.store(test_data, tmp_path, "output.csv")

    assert rows_written == 1

    # Verify file content
    result_file = tmp_path / "output.csv"
    content = result_file.read_text()
    assert "Charlie" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_async_csv_handler.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncCsvHandler'`

- [ ] **Step 3: Implement AsyncCsvHandler in dal/csv_handler.py**

Add to `dal/csv_handler.py` (after `CsvHandler` class):

```python
import aiofiles
import csv
from io import StringIO
# ... existing imports ...

# ... existing CsvHandler class ...

class AsyncCsvHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for CSV format files."""

    def __init__(self, delimiter: str = ",", encoding: str = "utf-8"):
        """Initialize AsyncCsvHandler.

        Args:
            delimiter: Character used to separate values (default: comma)
            encoding: Character encoding for file operations (default: utf-8)
        """
        self.delimiter = delimiter
        self.encoding = encoding

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
        """Fetch data from CSV file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            # Async file I/O
            async with aiofiles.open(file_path, "r", encoding=self.encoding, newline="") as f:
                content = await f.read()

            # Parse CSV
            reader = csv.DictReader(StringIO(content), delimiter=self.delimiter)
            data = list(reader)

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
        overwrite: bool = True,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to CSV file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            if not data_to_store:
                return 0

            # Get headers from first row
            fieldnames = list(data_to_store[0].keys())

            # Generate CSV content
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data_to_store)
            content = output.getvalue()

            # Write to file
            async with aiofiles.open(file_path, "w", encoding=self.encoding, newline="") as f:
                await f.write(content)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_csv_handler.py -v`

Expected: PASS (2 tests)

- [ ] **Step 5: Update dal/__init__.py to export AsyncCsvHandler**

Add to `dal/__init__.py`:

```python
from .csv_handler import CsvHandler, AsyncCsvHandler
```

- [ ] **Step 6: Commit**

```bash
git add dal/csv_handler.py dal/__init__.py tests/unit/test_async_csv_handler.py
git commit -m "feat: implement AsyncCsvHandler with async file I/O"
```

---

### Task 5: Implement AsyncPklHandler

**Files:**
- Modify: `dal/pkl_handler.py`
- Create: `tests/unit/test_async_pkl_handler.py`

- [ ] **Step 1: Write failing test for AsyncPklHandler**

Create: `tests/unit/test_async_pkl_handler.py`

```python
import pytest
from pathlib import Path
from data_access_layer.pkl_handler import AsyncPklHandler

@pytest.mark.asyncio
async def test_async_pkl_fetch_basic(tmp_path):
    """Test basic async fetch from pickle file."""
    import pickle
    test_file = tmp_path / "test.pkl"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_bytes(pickle.dumps(test_data))

    handler = AsyncPklHandler()
    result = await handler.fetch(tmp_path, "test.pkl")

    assert result == test_data

@pytest.mark.asyncio
async def test_async_pkl_store_basic(tmp_path):
    """Test basic async store to pickle file."""
    import pickle
    handler = AsyncPklHandler()
    test_data = [{"name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, tmp_path, "output.pkl")

    assert rows_written == 1

    # Verify file content
    result_file = tmp_path / "output.pkl"
    result = pickle.loads(result_file.read_bytes())
    assert result == test_data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_async_pkl_handler.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncPklHandler'`

- [ ] **Step 3: Implement AsyncPklHandler in dal/pkl_handler.py**

Add to `dal/pkl_handler.py` (after `PklHandler` class):

```python
import aiofiles
import asyncio
import pickle
# ... existing imports ...

# ... existing PklHandler class ...

class AsyncPklHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for Python pickle format files."""

    def __init__(self, protocol: int = 4):
        """Initialize AsyncPklHandler.

        Args:
            protocol: Pickle protocol version to use (default: 4)
        """
        self.protocol = protocol

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
        """Fetch data from pickle file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            # Async file I/O with pickle in thread pool
            def _load_pickle():
                with open(file_path, "rb") as f:
                    return pickle.load(f)

            data = await asyncio.to_thread(_load_pickle)

            if not isinstance(data, list):
                raise ValueError(
                    f"Pickle file must contain a list of objects, got {type(data).__name__}"
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
        overwrite: bool = True,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to pickle file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            # Write using thread pool (pickle is CPU-bound)
            def _dump_pickle():
                with open(file_path, "wb") as f:
                    pickle.dump(data_to_store, f, protocol=self.protocol)
                return len(data_to_store)

            return await asyncio.to_thread(_dump_pickle)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_pkl_handler.py -v`

Expected: PASS (2 tests)

- [ ] **Step 5: Update dal/__init__.py to export AsyncPklHandler**

Add to `dal/__init__.py`:

```python
from .pkl_handler import PklHandler, AsyncPklHandler
```

- [ ] **Step 6: Commit**

```bash
git add dal/pkl_handler.py dal/__init__.py tests/unit/test_async_pkl_handler.py
git commit -m "feat: implement AsyncPklHandler with async file I/O"
```

---

### Task 6: Implement AsyncXlsxHandler

**Files:**
- Modify: `dal/xlsx_handler.py`
- Create: `tests/unit/test_async_xlsx_handler.py`

- [ ] **Step 1: Write failing test for AsyncXlsxHandler**

Create: `tests/unit/test_async_xlsx_handler.py`

```python
import pytest
from pathlib import Path
from data_access_layer.xlsx_handler import AsyncXlsxHandler

@pytest.mark.asyncio
async def test_async_xlsx_fetch_basic(tmp_path):
    """Test basic async fetch from XLSX file."""
    from openpyxl import Workbook
    test_file = tmp_path / "test.xlsx"

    # Create test file
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "age"])
    ws.append(["Alice", 30])
    ws.append(["Bob", 25])
    wb.save(test_file)

    handler = AsyncXlsxHandler()
    result = await handler.fetch(tmp_path, "test.xlsx")

    assert len(result) == 2
    assert result[0] == {"name": "Alice", "age": 30}

@pytest.mark.asyncio
async def test_async_xlsx_store_basic(tmp_path):
    """Test basic async store to XLSX file."""
    handler = AsyncXlsxHandler()
    test_data = [{"name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, tmp_path, "output.xlsx")

    assert rows_written == 1

    # Verify file exists and can be read
    from openpyxl import load_workbook
    result_file = tmp_path / "output.xlsx"
    wb = load_workbook(result_file)
    ws = wb.active
    assert ws["A1"].value == "name"
    assert ws["A2"].value == "Charlie"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_async_xlsx_handler.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncXlsxHandler'`

- [ ] **Step 3: Implement AsyncXlsxHandler in dal/xlsx_handler.py**

Add to `dal/xlsx_handler.py` (after `XlsxHandler` class):

```python
import aiofiles
import asyncio
from openpyxl import load_workbook, Workbook
from openpyxl.utils.exceptions import InvalidFileException
# ... existing imports ...

# ... existing XlsxHandler class ...

class AsyncXlsxHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for Excel XLSX format files."""

    def __init__(self, sheet_name: str = "Sheet1", header_row: int = 0):
        """Initialize AsyncXlsxHandler.

        Args:
            sheet_name: Name of sheet to read/write (default: "Sheet1")
            header_row: Row index containing column headers (default: 0)
        """
        self.sheet_name = sheet_name
        self.header_row = header_row

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
        """Fetch data from XLSX file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            # Load workbook in thread pool (openpyxl is CPU-bound)
            def _load_workbook():
                wb = load_workbook(file_path)
                if self.sheet_name not in wb.sheetnames:
                    raise ValueError(f"Sheet '{self.sheet_name}' not found in workbook")
                ws = wb[self.sheet_name]

                # Get headers
                headers = [cell.value for cell in ws[self.header_row + 1]]

                # Get data
                data = []
                for row in ws.iter_rows(min_row=self.header_row + 2):
                    row_data = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers)}
                    if any(v is not None for v in row_data.values()):
                        data.append(row_data)

                wb.close()
                return data

            data = await asyncio.to_thread(_load_workbook)

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
        overwrite: bool = True,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,
    ) -> int:
        """Store data to XLSX file asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            if not data_to_store:
                return 0

            # Write workbook in thread pool (openpyxl is CPU-bound)
            def _write_workbook():
                wb = Workbook()
                ws = wb.active
                ws.title = self.sheet_name

                # Write headers
                headers = list(data_to_store[0].keys())
                ws.append(headers)

                # Write data
                for row in data_to_store:
                    ws.append([row.get(h) for h in headers])

                wb.save(file_path)
                wb.close()
                return len(data_to_store)

            return await asyncio.to_thread(_write_workbook)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_xlsx_handler.py -v`

Expected: PASS (2 tests)

- [ ] **Step 5: Update dal/__init__.py to export AsyncXlsxHandler**

Add to `dal/__init__.py`:

```python
from .xlsx_handler import XlsxHandler, AsyncXlsxHandler
```

- [ ] **Step 6: Commit**

```bash
git add dal/xlsx_handler.py dal/__init__.py tests/unit/test_async_xlsx_handler.py
git commit -m "feat: implement AsyncXlsxHandler with async file I/O"
```

---

### Task 7: Implement AsyncSqliteHandler

**Files:**
- Modify: `dal/sqlite_handler.py`
- Create: `tests/unit/test_async_sqlite_handler.py`

- [ ] **Step 1: Write failing test for AsyncSqliteHandler**

Create: `tests/unit/test_async_sqlite_handler.py`

```python
import pytest
from pathlib import Path
from data_access_layer.sqlite_handler import AsyncSqliteHandler

@pytest.mark.asyncio
async def test_async_sqlite_fetch_basic(tmp_path):
    """Test basic async fetch from SQLite database."""
    import sqlite3

    # Create test database
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 25)")
    conn.commit()
    conn.close()

    handler = AsyncSqliteHandler()
    result = await handler.fetch(db_file, "users")

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Alice", "age": 30}

@pytest.mark.asyncio
async def test_async_sqlite_store_basic(tmp_path):
    """Test basic async store to SQLite database."""
    import sqlite3

    # Create test database with table
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
    conn.commit()
    conn.close()

    handler = AsyncSqliteHandler()
    test_data = [{"id": 3, "name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, db_file, "users")

    assert rows_written == 1

    # Verify
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = 3")
    result = cursor.fetchone()
    conn.close()
    assert result == (3, "Charlie", 35)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_async_sqlite_handler.py -v`

Expected: FAIL with `ImportError: cannot import name 'AsyncSqliteHandler'`

- [ ] **Step 3: Implement AsyncSqliteHandler in dal/sqlite_handler.py**

Add to `dal/sqlite_handler.py` (after `SqliteHandler` class):

```python
import aiosqlite
# ... existing imports ...

# ... existing SqliteHandler class ...

class AsyncSqliteHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for SQLite databases."""

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
        """Fetch data from SQLite table asynchronously."""
        # Note: This is a sync wrapper - actual implementation uses async
        raise NotImplementedError("Use async fetch")

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
        """Fetch data from SQLite table asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            async with aiosqlite.connect(path) as conn:
                cursor = await conn.cursor()

                # Check if table exists
                await cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if await cursor.fetchone() is None:
                    raise Exception(f"Table '{table}' does not exist in database '{path}'")

                # Fetch all data
                await cursor.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]

            # Apply post-processing (types, cols, filter, limit)
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
        """Store data to SQLite table asynchronously."""
        # Note: This is a sync wrapper - actual implementation uses async
        raise NotImplementedError("Use async store")

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
        """Store data to SQLite table asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            async with aiosqlite.connect(path) as conn:
                cursor = await conn.cursor()

                # Check if table exists
                await cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if await cursor.fetchone() is None:
                    raise Exception(f"Table '{table}' does not exist in database '{path}'")

                # Get table columns
                await cursor.execute(f"PRAGMA table_info({table})")
                table_columns_rows = await cursor.fetchall()
                table_columns = {row[1] for row in table_columns_rows}

                # Prepare data to store
                data_to_store = data.copy()

                # Apply post-processing (types, cols, filter, limit)
                data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

                # Clear table if overwrite mode
                if overwrite:
                    await cursor.execute(f"DELETE FROM {table}")

                # Insert data
                if data_to_store:
                    for row in data_to_store:
                        columns_to_insert = [k for k in row.keys() if k in table_columns]
                        if not columns_to_insert:
                            continue
                        placeholders = ", ".join(["?"] * len(columns_to_insert))
                        columns_str = ", ".join(columns_to_insert)
                        values = [row.get(col) for col in columns_to_insert]
                        await cursor.execute(
                            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                            values
                        )

                await conn.commit()

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

Wait, there's a duplicate method definition issue. Let me fix the implementation:

- [ ] **Step 3 (revised): Implement AsyncSqliteHandler correctly**

The correct implementation should only have async methods:

```python
import aiosqlite
# ... existing imports ...

# ... existing SqliteHandler class ...

class AsyncSqliteHandler(PostProcessingMixin, AsyncDataHandler):
    """Async handler for SQLite databases using aiosqlite."""

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
        """Fetch data from SQLite table asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            async with aiosqlite.connect(path) as conn:
                cursor = await conn.cursor()

                # Check if table exists
                await cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if await cursor.fetchone() is None:
                    raise Exception(f"Table '{table}' does not exist in database '{path}'")

                # Fetch all data
                await cursor.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]

            # Apply post-processing (types, cols, filter, limit)
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
        """Store data to SQLite table asynchronously."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Database file '{path}' does not exist")

            async with aiosqlite.connect(path) as conn:
                cursor = await conn.cursor()

                # Check if table exists
                await cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if await cursor.fetchone() is None:
                    raise Exception(f"Table '{table}' does not exist in database '{path}'")

                # Get table columns
                await cursor.execute(f"PRAGMA table_info({table})")
                table_columns_rows = await cursor.fetchall()
                table_columns = {row[1] for row in table_columns_rows}

                # Prepare data to store
                data_to_store = data.copy()

                # Apply post-processing (types, cols, filter, limit)
                data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

                # Clear table if overwrite mode
                if overwrite:
                    await cursor.execute(f"DELETE FROM {table}")

                # Insert data
                if data_to_store:
                    for row in data_to_store:
                        columns_to_insert = [k for k in row.keys() if k in table_columns]
                        if not columns_to_insert:
                            continue
                        placeholders = ", ".join(["?"] * len(columns_to_insert))
                        columns_str = ", ".join(columns_to_insert)
                        values = [row.get(col) for col in columns_to_insert]
                        await cursor.execute(
                            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                            values
                        )

                await conn.commit()

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_async_sqlite_handler.py -v`

Expected: PASS (2 tests)

- [ ] **Step 5: Update dal/__init__.py to export AsyncSqliteHandler**

Add to `dal/__init__.py`:

```python
from .sqlite_handler import SqliteHandler, AsyncSqliteHandler
```

- [ ] **Step 6: Commit**

```bash
git add dal/sqlite_handler.py dal/__init__.py tests/unit/test_async_sqlite_handler.py
git commit -m "feat: implement AsyncSqliteHandler with aiosqlite"
```

---

### Task 8: Update README.md with async documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add async installation instructions**

Add to README.md installation section:

```markdown
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

# Install with async support
poetry add data-access-layer --extras async
```
```

- [ ] **Step 2: Add async usage section**

Add to README.md after the basic usage section:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add async usage documentation to README"
```

---

### Task 9: Run full test suite and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run all async tests**

Run: `pytest tests/unit/test_async_*.py -v`

Expected: PASS (all async handler tests)

- [ ] **Step 2: Run full test suite to ensure no regressions**

Run: `pytest -v`

Expected: PASS (all tests, including existing sync tests)

- [ ] **Step 3: Run type checking**

Run: `mypy dal`

Expected: PASS (no type errors)

- [ ] **Step 4: Verify exports work**

Run: `python -c "from dal import JsonHandler, AsyncJsonHandler, CsvHandler, AsyncCsvHandler, PklHandler, AsyncPklHandler, XlsxHandler, AsyncXlsxHandler, SqliteHandler, AsyncSqliteHandler; print('All exports OK')"`

Expected: "All exports OK"

- [ ] **Step 5: Final verification commit**

```bash
git add -A
git commit -m "chore: verify async support implementation complete"
```

---

## Self-Review

**Spec coverage check:**
- ✓ AsyncDataHandler ABC — Task 2
- ✓ AsyncJsonHandler — Task 3
- ✓ AsyncCsvHandler — Task 4
- ✓ AsyncPklHandler — Task 5
- ✓ AsyncXlsxHandler — Task 6
- ✓ AsyncSqliteHandler — Task 7
- ✓ Dependencies (aiofiles, aiosqlite) — Task 1
- ✓ Testing strategy (async I/O tests) — All handler tasks
- ✓ Documentation — Task 8
- ✓ Final verification — Task 9

**Placeholder scan:**
- No TBD/TODO found
- All code blocks contain complete implementations
- All test cases have full assertions
- All file paths are explicit

**Type consistency:**
- Method signatures match AsyncDataHandler ABC
- Consistent parameter names across all handlers
- Consistent use of `types` parameter for type coercion

---

Plan complete and saved to `docs/superpowers/plans/2026-05-09-async-support.md`.
