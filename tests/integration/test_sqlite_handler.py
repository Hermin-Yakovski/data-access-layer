from pathlib import Path
import pytest
import sqlite3

from dal.sqlite_handler import SqliteHandler


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

        handler = SqliteHandler()
        with pytest.raises(Exception):  # sqlite3.OperationalError wrapped
            handler.fetch(path=temp_db, table="nonexistent_table", strict=True)

    def test_fetch_returns_empty_list_when_table_missing_strict_false(self, temp_db):
        """When table doesn't exist and strict=False, return empty list."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="nonexistent_table", strict=False)
        assert result == []

    def test_fetch_from_real_table(self, temp_db):
        """Fetch data from an actual SQLite table."""
        # Create test table with data
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users")
        assert len(result) == 2
        assert {"name": "Alice", "age": 30, "id": 1} in result
        assert {"name": "Bob", "age": 25, "id": 2} in result

    def test_fetch_empty_table(self, temp_db):
        """Fetch from an empty table returns empty list."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users")
        assert result == []

    def test_fetch_with_column_selection(self, temp_db):
        """Fetch with column allowlist - only specified columns included."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.execute("INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@test.com')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", cols=["name", "age"])
        # Only the specified columns are included (id and email are excluded)
        assert result == [{"name": "Alice", "age": 30}]

    def test_fetch_with_filter(self, temp_db):
        """Filter is applied to rows."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", filter_=lambda row: row["age"] > 25)
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

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", limit=1)
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

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table="users",
            filter_=lambda row: row["age"] >= 30,
            limit=1
        )
        # Two rows match filter, but only 1 returned due to limit
        assert len(result) == 1
