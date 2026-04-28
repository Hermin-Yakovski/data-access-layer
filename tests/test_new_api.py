# tests/test_new_api.py
"""Tests for the new XlsxHandler API.

This file tests the redesigned XlsxHandler API where:
- __init__ only takes header_row parameter (not sheet_name)
- sheet_name is specified via the table parameter in fetch() and store()
"""
from pathlib import Path
import pytest

try:
    from dal.xlsx_handler import XlsxHandler
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestNewAPI:
    """Tests for the redesigned XlsxHandler API."""

    def test_init_accepts_only_header_row(self):
        """XlsxHandler.__init__ should accept only header_row parameter."""
        # Should work with default header_row
        handler = XlsxHandler()
        assert hasattr(handler, 'header_row')
        assert handler.header_row == 0

        # Should work with explicit header_row
        handler = XlsxHandler(header_row=1)
        assert handler.header_row == 1

    def test_init_does_not_accept_sheet_name(self):
        """XlsxHandler.__init__ should not accept sheet_name parameter."""
        # This should raise TypeError due to unexpected keyword argument
        with pytest.raises(TypeError, match="sheet_name"):
            handler = XlsxHandler(sheet_name="MySheet")

    def test_init_does_not_have_sheet_name_attribute(self):
        """XlsxHandler instance should not have sheet_name attribute."""
        handler = XlsxHandler()
        assert not hasattr(handler, 'sheet_name')

    def test_fetch_uses_path_as_file_path_and_table_as_sheet_name(self, tmp_path):
        """fetch() should use path as file path and table as sheet name."""
        from openpyxl import Workbook

        # Create a test file with multiple sheets
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Users"
        ws1.append(["name", "age"])
        ws1.append(["Alice", 30])

        ws2 = wb.create_sheet("Products")
        ws2.append(["product", "price"])
        ws2.append(["Widget", 9.99])

        # Save to a specific file path
        test_file = tmp_path / "data.xlsx"
        wb.save(test_file)

        # Test fetching with path as file and table as sheet
        handler = XlsxHandler()

        # Fetch from Users sheet
        users = handler.fetch(path=test_file, table="Users")
        assert users == [{"name": "Alice", "age": 30}]

        # Fetch from Products sheet
        products = handler.fetch(path=test_file, table="Products")
        assert products == [{"product": "Widget", "price": 9.99}]

    def test_fetch_raises_error_when_file_not_found(self, tmp_path):
        """fetch() should raise FileNotFoundError when file path doesn't exist."""
        handler = XlsxHandler()
        nonexistent_file = tmp_path / "nonexistent.xlsx"

        with pytest.raises(FileNotFoundError, match="does not exist"):
            handler.fetch(path=nonexistent_file, table="Sheet1")
