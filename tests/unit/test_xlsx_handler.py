# tests/unit/test_xlsx_handler.py
from pathlib import Path
import pytest

try:
    from dal.xlsx_handler import XlsxHandler
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerFetch:
    """Unit tests for XlsxHandler.fetch() method."""

    def test_fetch_returns_empty_list_when_strict_false_and_file_not_found(self):
        """When strict=False and file not found, return empty list."""
        handler = XlsxHandler()
        result = handler.fetch(
            path=Path("nonexistent"),
            table="data.xlsx",
            strict=False
        )
        assert result == []

    def test_fetch_raises_file_not_found_when_strict_true(self):
        """When strict=True and file not found, raise FileNotFoundError."""
        handler = XlsxHandler()
        with pytest.raises(FileNotFoundError):
            handler.fetch(
                path=Path("nonexistent"),
                table="data.xlsx",
                strict=True
            )

    # Note: More complex fetch tests are in integration tests due to mocking complexity


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerStore:
    """Unit tests for XlsxHandler.store() method."""

    def test_store_returns_zero_when_strict_false_and_path_not_found(self):
        """When strict=False and path doesn't exist, return 0."""
        handler = XlsxHandler()
        result = handler.store(
            data=[{"name": "Alice"}],
            path=Path("nonexistent"),
            table="output.xlsx",
            strict=False
        )
        assert result == 0

    def test_store_raises_file_not_found_when_strict_true(self):
        """When strict=True and path doesn't exist, raise FileNotFoundError."""
        handler = XlsxHandler()
        with pytest.raises(FileNotFoundError):
            handler.store(
                data=[{"name": "Alice"}],
                path=Path("nonexistent"),
                table="output.xlsx",
                strict=True
            )

    # Note: More complex store tests are in integration tests due to mocking complexity
