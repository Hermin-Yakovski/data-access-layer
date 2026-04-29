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
