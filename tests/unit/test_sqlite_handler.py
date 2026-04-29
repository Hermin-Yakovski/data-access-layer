from pathlib import Path
import pytest

from dal.sqlite_handler import SqliteHandler


class TestSqliteHandlerInit:
    """Unit tests for SqliteHandler.__init__ method."""

    def test_sqlite_handler_can_be_instantiated(self):
        """SqliteHandler can be instantiated without parameters."""
        handler = SqliteHandler()
        assert handler is not None

    def test_sqlite_handler_exported_from_dal_package(self):
        """SqliteHandler should be importable from dal package."""
        from dal import SqliteHandler
        assert SqliteHandler is not None


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
