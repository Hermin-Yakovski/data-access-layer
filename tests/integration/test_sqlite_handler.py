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
