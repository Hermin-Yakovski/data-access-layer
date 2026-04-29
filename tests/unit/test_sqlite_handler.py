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
