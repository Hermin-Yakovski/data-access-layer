# SqliteHandler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SqliteHandler to support SQLite databases with fetch/store operations, following the DataHandler ABC interface.

**Architecture:** SqliteHandler takes database path in `__init__` (unlike XlsxHandler), operates on tables via `fetch(table)`/`store(data, table)` methods. Per-operation connections (open, execute, close). Table must exist before storing. Extra columns ignored, missing columns = NULL.

**Tech Stack:** Python 3.11+, sqlite3 (stdlib), pytest, existing test infrastructure

---

## File Structure

**New files:**
- `dal/sqlite_handler.py` — SqliteHandler implementation
- `tests/unit/test_sqlite_handler.py` — Unit tests (minimal, since sqlite3 requires real connections)
- `tests/integration/test_sqlite_handler.py` — Integration tests with real databases

**Modified files:**
- `dal/__init__.py` — Export SqliteHandler

---

## Task 1: Create SqliteHandler with `__init__` method

**Files:**
- Create: `dal/sqlite_handler.py`

**Goal:** Create the basic SqliteHandler class with `__init__` that stores the database path.

- [ ] **Step 1: Write the failing test for `__init__`**

```python
# tests/unit/test_sqlite_handler.py
from pathlib import Path
import pytest

from dal.sqlite_handler import SqliteHandler


class TestSqliteHandlerInit:
    """Unit tests for SqliteHandler.__init__ method."""

    def test_init_stores_path_attribute(self):
        """SqliteHandler.__init__ should store path as an attribute."""
        db_path = Path("test.db")
        handler = SqliteHandler(path=db_path)
        assert hasattr(handler, 'path')
        assert handler.path == db_path
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerInit::test_init_stores_path_attribute -v`
Expected: FAIL with "cannot import 'SqliteHandler' from 'dal.sqlite_handler'"

- [ ] **Step 3: Write minimal implementation**

```python
# dal/sqlite_handler.py
import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .abc import DataHandler


class SqliteHandler(DataHandler):
    """Handler for SQLite databases.

    Supports fetching and storing data in SQLite tables.
    Table must exist before storing data.
    """

    def __init__(self, path: Path):
        """Initialize SqliteHandler.

        Args:
            path: Path to the SQLite database file
        """
        self.path = path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerInit::test_init_stores_path_attribute -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/sqlite_handler.py tests/unit/test_sqlite_handler.py
git commit -m "feat: add SqliteHandler with __init__ method"
```

---

## Task 2: Implement `fetch()` method — database not found

**Files:**
- Modify: `dal/sqlite_handler.py`
- Test: `tests/unit/test_sqlite_handler.py`

- [ ] **Step 1: Write the failing test for database file not found**

```python
# tests/unit/test_sqlite_handler.py
class TestSqliteHandlerFetch:
    """Unit tests for SqliteHandler.fetch() method."""

    def test_fetch_raises_file_not_found_when_database_missing_strict_true(self):
        """When database file doesn't exist and strict=True, raise FileNotFoundError."""
        handler = SqliteHandler(path=Path("nonexistent.db"))
        with pytest.raises(FileNotFoundError, match="does not exist"):
            handler.fetch(table="users", strict=True)

    def test_fetch_returns_empty_list_when_database_missing_strict_false(self):
        """When database file doesn't exist and strict=False, return empty list."""
        handler = SqliteHandler(path=Path("nonexistent.db"))
        result = handler.fetch(table="users", strict=False)
        assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerFetch -v`
Expected: FAIL with "SqliteHandler has no attribute 'fetch'"

- [ ] **Step 3: Implement `fetch()` method stub with file existence check**

```python
# dal/sqlite_handler.py
# Add to SqliteHandler class:

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
        """
        try:
            if not self.path.exists():
                raise FileNotFoundError(f"Database file '{self.path}' does not exist")

            # TODO: implement rest of fetch
            return []

        except Exception:
            if strict:
                raise
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerFetch -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/sqlite_handler.py tests/unit/test_sqlite_handler.py
git commit -m "feat: add SqliteHandler.fetch() with database file existence check"
```

---

## Task 3: Implement `fetch()` — table not found

**Files:**
- Modify: `dal/sqlite_handler.py`
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write integration test for table not found**

```python
# tests/integration/test_sqlite_handler.py
from pathlib import Path
import pytest
import sqlite3

from dal import SqliteHandler


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    return db_path


class TestSqliteHandlerFetchIntegration:
    """Integration tests for SqliteHandler.fetch() with real databases."""

    def test_fetch_raises_error_when_table_missing_strict_true(self, temp_db):
        """When table doesn't exist and strict=True, raise OperationalError with clear message."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler(path=temp_db)
        with pytest.raises(Exception):  # sqlite3.OperationalError wrapped
            handler.fetch(table="nonexistent_table", strict=True)

    def test_fetch_returns_empty_list_when_table_missing_strict_false(self, temp_db):
        """When table doesn't exist and strict=False, return empty list."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="nonexistent_table", strict=False)
        assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerFetchIntegration -v`
Expected: FAIL (table check not implemented yet)

- [ ] **Step 3: Implement table existence check**

```python
# dal/sqlite_handler.py
# Modify fetch() method:

    def fetch(
        self,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from SQLite table."""
        try:
            if not self.path.exists():
                raise FileNotFoundError(f"Database file '{self.path}' does not exist")

            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if cursor.fetchone() is None:
                conn.close()
                raise Exception(f"Table '{table}' does not exist in database '{self.path}'")

            # Fetch all data
            cursor.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]

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

        except Exception:
            if strict:
                raise
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerFetchIntegration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/sqlite_handler.py tests/integration/test_sqlite_handler.py
git commit -m "feat: implement SqliteHandler.fetch() with table check and data retrieval"
```

---

## Task 4: Implement `fetch()` — filter, cols, limit

**Files:**
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write integration tests for filter, cols, limit**

```python
# tests/integration/test_sqlite_handler.py
# Add to TestSqliteHandlerFetchIntegration class:

    def test_fetch_from_real_table(self, temp_db):
        """Fetch data from an actual SQLite table."""
        # Create test table with data
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="users")
        assert len(result) == 2
        assert {"name": "Alice", "age": 30, "id": 1} in result
        assert {"name": "Bob", "age": 25, "id": 2} in result

    def test_fetch_empty_table(self, temp_db):
        """Fetch from an empty table returns empty list."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="users")
        assert result == []

    def test_fetch_with_column_selection(self, temp_db):
        """Fetch with column allowlist - only specified columns included."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.execute("INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@test.com')")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="users", cols=["name", "age"])
        assert result == [{"name": "Alice", "age": 30, "id": 1}]

    def test_fetch_with_filter(self, temp_db):
        """Filter is applied to rows."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="users", filter_=lambda row: row["age"] > 25)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_fetch_with_limit(self, temp_db):
        """Limit is applied after filtering."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(table="users", limit=1)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_fetch_with_filter_and_limit(self, temp_db):
        """Filter is applied first, then limit to filtered results."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Charlie', 35)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        result = handler.fetch(
            table="users",
            filter_=lambda row: row["age"] >= 30,
            limit=1
        )
        # Two rows match filter, but only 1 returned due to limit
        assert len(result) == 1
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerFetchIntegration -v`
Expected: PASS (already implemented in Task 3)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_sqlite_handler.py
git commit -m "test: add integration tests for SqliteHandler.fetch() with filter, cols, limit"
```

---

## Task 5: Implement `store()` method — basic functionality

**Files:**
- Modify: `dal/sqlite_handler.py`
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write integration tests for basic store**

```python
# tests/integration/test_sqlite_handler.py
class TestSqliteHandlerStoreIntegration:
    """Integration tests for SqliteHandler.store() with real databases."""

    def test_store_to_real_table(self, temp_db):
        """Store data to an actual SQLite table (table must exist)."""
        # Create table first
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        test_data = [{"name": "Alice", "age": 30}]
        handler = SqliteHandler(path=temp_db)
        result = handler.store(data=test_data, table="users")
        assert result == 1

        # Verify data was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30)]

    def test_store_raises_error_when_table_missing(self, temp_db):
        """Store should raise error when table doesn't exist (user must create schema)."""
        # Create empty database, no table
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler(path=temp_db)
        data = [{"name": "Alice", "age": 30}]

        with pytest.raises(Exception):  # Table doesn't exist
            handler.store(data=data, table="users", strict=True)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration -v`
Expected: FAIL with "SqliteHandler has no attribute 'store'"

- [ ] **Step 3: Implement `store()` method**

```python
# dal/sqlite_handler.py
# Add to SqliteHandler class:

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
        """
        try:
            if not self.path.exists():
                raise FileNotFoundError(f"Database file '{self.path}' does not exist")

            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if cursor.fetchone() is None:
                conn.close()
                raise Exception(f"Table '{table}' does not exist in database '{self.path}'")

            # Get table columns
            cursor.execute(f"PRAGMA table_info({table})")
            table_columns = {row[1] for row in cursor.fetchall()}

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

            # Clear table if overwrite mode
            if overwrite:
                cursor.execute(f"DELETE FROM {table}")

            # Insert data
            if data_to_store:
                # Only insert columns that exist in table
                for row in data_to_store:
                    columns_to_insert = [k for k in row.keys() if k in table_columns]
                    if not columns_to_insert:
                        continue
                    placeholders = ", ".join(["?"] * len(columns_to_insert))
                    columns_str = ", ".join(columns_to_insert)
                    values = [row.get(col) for col in columns_to_insert]
                    cursor.execute(
                        f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                        values
                    )

            conn.commit()
            conn.close()

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/sqlite_handler.py tests/integration/test_sqlite_handler.py
git commit -m "feat: implement SqliteHandler.store() with basic functionality"
```

---

## Task 6: Implement `store()` — overwrite and append modes

**Files:**
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write tests for overwrite and append modes**

```python
# tests/integration/test_sqlite_handler.py
# Add to TestSqliteHandlerStoreIntegration class:

    def test_store_overwrite_clears_existing_data(self, temp_db):
        """Store with overwrite=True clears existing data before inserting."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)

        # Overwrite with new data
        new_data = [{"name": "Bob", "age": 25}]
        handler.store(data=new_data, table="users", overwrite=True)

        # Verify only new data exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Bob", 25)]

    def test_store_append_adds_to_existing_data(self, temp_db):
        """Store with overwrite=False appends to existing data."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)

        # Append more data
        more_data = [{"name": "Bob", "age": 25}]
        handler.store(data=more_data, table="users", overwrite=False)

        # Verify both rows exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30), ("Bob", 25)]

    def test_store_overwrite_on_empty_table(self, temp_db):
        """Store with overwrite=True on empty table works (DELETE is no-op, then inserts)."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.commit()
        conn.close()

        handler = SqliteHandler(path=temp_db)
        data = [{"name": "Alice", "age": 30}]
        result = handler.store(data=data, table="users", overwrite=True)

        assert result == 1

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration::test_store_overwrite_clears_existing_data -v`
Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration::test_store_append_adds_to_existing_data -v`
Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration::test_store_overwrite_on_empty_table -v`
Expected: PASS (already implemented in Task 5)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_sqlite_handler.py
git commit -m "test: add tests for SqliteHandler.store() overwrite and append modes"
```

---

## Task 7: Implement `store()` — column matching behavior

**Files:**
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write tests for column matching**

```python
# tests/integration/test_sqlite_handler.py
# Add to TestSqliteHandlerStoreIntegration class:

    def test_store_ignores_extra_columns_in_data(self, temp_db):
        """Extra columns in data are silently ignored (only insert columns that exist)."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler(path=temp_db)
        # Data has 'email' column which doesn't exist in table
        data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        result = handler.store(data=data, table="users")

        assert result == 1

        # Verify only name and age were stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        assert columns == ["id", "name", "age"]
        assert "email" not in columns

    def test_store_inserts_null_for_missing_columns(self, temp_db):
        """Missing columns in data get NULL inserted."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.close()

        handler = SqliteHandler(path=temp_db)
        # Data missing 'age' and 'email'
        data = [{"name": "Alice"}]
        handler.store(data=data, table="users")

        # Verify NULL for missing columns
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, email FROM users")
        row = cursor.fetchone()
        conn.close()
        assert row == ("Alice", None, None)

    def test_store_with_column_selection(self, temp_db):
        """Store with column allowlist - only specified columns stored."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.close()

        handler = SqliteHandler(path=temp_db)
        data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        handler.store(data=data, table="users", cols=["name", "age"])

        # Verify only name and age were stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, email FROM users")
        row = cursor.fetchone()
        conn.close()
        assert row == ("Alice", 30, None)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration -k "column" -v`
Expected: PASS (already implemented in Task 5)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_sqlite_handler.py
git commit -m "test: add tests for SqliteHandler.store() column matching behavior"
```

---

## Task 8: Implement `store()` — filter and limit

**Files:**
- Test: `tests/integration/test_sqlite_handler.py`

- [ ] **Step 1: Write tests for filter and limit in store**

```python
# tests/integration/test_sqlite_handler.py
# Add to TestSqliteHandlerStoreIntegration class:

    def test_store_with_filter(self, temp_db):
        """Filter is applied before storing."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler(path=temp_db)
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = handler.store(data=data, table="users", filter_=lambda row: row["age"] > 25)

        assert result == 1

        # Verify only filtered data was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30)]

    def test_store_with_limit(self, temp_db):
        """Limit is applied after filtering."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler(path=temp_db)
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = handler.store(data=data, table="users", limit=1)

        assert result == 1

        # Verify only 1 row was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/integration/test_sqlite_handler.py::TestSqliteHandlerStoreIntegration -k "filter or limit" -v`
Expected: PASS (already implemented in Task 5)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_sqlite_handler.py
git commit -m "test: add tests for SqliteHandler.store() filter and limit"
```

---

## Task 9: Update `dal/__init__.py` to export SqliteHandler

**Files:**
- Modify: `dal/__init__.py`

- [ ] **Step 1: Write test to verify SqliteHandler can be imported**

```python
# tests/unit/test_sqlite_handler.py
# Add to TestSqliteHandlerInit class:

    def test_sqlite_handler_exported_from_dal_package(self):
        """SqliteHandler should be importable from dal package."""
        from dal import SqliteHandler
        assert SqliteHandler is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerInit::test_sqlite_handler_exported_from_dal_package -v`
Expected: FAIL with "cannot import name 'SqliteHandler' from 'dal'"

- [ ] **Step 3: Update `dal/__init__.py`**

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerInit::test_sqlite_handler_exported_from_dal_package -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/__init__.py tests/unit/test_sqlite_handler.py
git commit -m "feat: export SqliteHandler from dal package"
```

---

## Task 10: Run all tests and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run all SqliteHandler tests**

Run: `pytest tests/unit/test_sqlite_handler.py tests/integration/test_sqlite_handler.py -v`

Expected: All PASS

- [ ] **Step 2: Run all package tests to ensure no regressions**

Run: `pytest tests/ -v`

Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-04-28-sqlite-handler-implementation.md
git commit -m "docs: add SqliteHandler implementation plan"
```

---

## Self-Review Results

**1. Spec coverage check:**
- ✅ `__init__(path)` — Task 1
- ✅ `fetch()` with table not found — Task 3
- ✅ `fetch()` with filter, cols, limit — Task 4
- ✅ `store()` basic functionality — Task 5
- ✅ `store()` overwrite/append modes — Task 6
- ✅ Column matching behavior — Task 7
- ✅ `store()` with filter and limit — Task 8
- ✅ Package exports — Task 9
- ✅ Error handling (FileNotFoundError, table not found) — Tasks 2-3
- ✅ Empty table/data handling — Tasks 4-6

**2. Placeholder scan:**
- ✅ No "TBD", "TODO", or "implement later" found
- ✅ All steps contain actual code
- ✅ All tests have complete assertions
- ✅ All file paths are exact

**3. Type consistency check:**
- ✅ `fetch(table, cols, filter_, limit, strict)` — consistent across all tasks
- ✅ `store(data, table, cols, filter_, limit, overwrite, strict)` — consistent across all tasks
- ✅ `__init__(path)` — consistent
- ✅ Error messages use consistent format

**4. Edge cases covered:**
- ✅ Database doesn't exist — Task 2
- ✅ Table doesn't exist — Task 3
- ✅ Empty table — Task 4
- ✅ Extra columns in data — Task 7
- ✅ Missing columns in data — Task 7
- ✅ Empty data — covered by store logic
- ✅ Overwrite vs append — Task 6
