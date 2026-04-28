# tests/unit/test_xlsx_handler.py
from pathlib import Path
import pytest

try:
    from dal.xlsx_handler import XlsxHandler
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerInit:
    """Unit tests for XlsxHandler.__init__ method."""

    def test_init_accepts_only_header_row(self):
        """XlsxHandler.__init__ should accept only header_row parameter."""
        handler = XlsxHandler()
        assert hasattr(handler, 'header_row')
        assert handler.header_row == 0

        handler = XlsxHandler(header_row=1)
        assert handler.header_row == 1

    def test_init_does_not_accept_sheet_name(self):
        """XlsxHandler.__init__ should not accept sheet_name parameter."""
        with pytest.raises(TypeError, match="sheet_name"):
            XlsxHandler(sheet_name="MySheet")

    def test_init_does_not_have_sheet_name_attribute(self):
        """XlsxHandler instance should not have sheet_name attribute."""
        handler = XlsxHandler()
        assert not hasattr(handler, 'sheet_name')


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerFetch:
    """Unit tests for XlsxHandler.fetch() method."""

    # Note: File-not-found behavior is tested in integration tests with proper temp directories.
    # Unit tests for fetch require real files due to openpyxl behavior.

    pass


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerStore:
    """Unit tests for XlsxHandler.store() method."""

    # Note: With the new API, store() creates files if they don't exist.
    # Parent directory not existing is tested in integration tests.
    # All other store tests require real files due to openpyxl behavior.

    pass
