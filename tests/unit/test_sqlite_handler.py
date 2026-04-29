from pathlib import Path
import pytest

from dal.sqlite_handler import SqliteHandler


class TestSqliteHandlerInit:
    """Unit tests for SqliteHandler.__init__ method."""

    def test_init_with_path_parameter(self):
        """SqliteHandler.__init__ should accept optional path parameter."""
        db_path = Path("test.db")
        handler = SqliteHandler(path=db_path)
        assert hasattr(handler, 'path')
        assert handler.path == db_path

    def test_init_without_path_parameter(self):
        """SqliteHandler.__init__ should work without path parameter."""
        handler = SqliteHandler()
        assert hasattr(handler, 'path')
        assert handler.path is None


class TestSqliteHandlerFetch:
    """Unit tests for SqliteHandler.fetch() method."""

    def test_fetch_raises_file_not_found_when_database_missing_strict_true(self):
        """When database file doesn't exist and strict=True, raise FileNotFoundError."""
        handler = SqliteHandler()
        db_path = Path("nonexistent.db")
        with pytest.raises(FileNotFoundError, match="does not exist"):
            handler.fetch(path=db_path, table="users", strict=True)

    def test_fetch_returns_empty_list_when_database_missing_strict_false(self):
        """When database file doesn't exist and strict=False, return empty list."""
        handler = SqliteHandler()
        db_path = Path("nonexistent.db")
        result = handler.fetch(path=db_path, table="users", strict=False)
        assert result == []
