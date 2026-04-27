# tests/unit/test_xlsx_handler.py
from pathlib import Path
from unittest.mock import MagicMock, patch
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

    @patch("dal.xlsx_handler.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_all_data(self, mock_exists, mock_load_wb):
        """Fetch returns all data when no filters specified."""
        # Mock workbook and worksheet
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ["name", "age"],
            ["Alice", 30],
            ["Bob", 25]
        ]
        mock_wb = MagicMock()
        mock_wb.__enter__ = MagicMock(return_value=mock_wb)
        mock_wb.__exit__ = MagicMock(return_value=False)
        mock_wb[sheet_name] = mock_ws
        mock_load_wb.return_value = mock_wb

        handler = XlsxHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.xlsx",
            sheet_name=sheet_name
        )
        assert result == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    @patch("dal.xlsx_handler.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter(self, mock_exists, mock_load_wb):
        """Filter is applied to rows before returning."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ["name", "age"],
            ["Alice", 30],
            ["Bob", 25]
        ]
        mock_wb = MagicMock()
        mock_wb.__enter__ = MagicMock(return_value=mock_wb)
        mock_wb.__exit__ = MagicMock(return_value=False)
        mock_wb[sheet_name] = mock_ws
        mock_load_wb.return_value = mock_wb

        handler = XlsxHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.xlsx",
            sheet_name=sheet_name,
            filter_=lambda row: row["age"] > 25
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("dal.xlsx_handler.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_limit(self, mock_exists, mock_load_wb):
        """Limit is applied after filtering."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ["name", "age"],
            ["Alice", 30],
            ["Bob", 25]
        ]
        mock_wb = MagicMock()
        mock_wb.__enter__ = MagicMock(return_value=mock_wb)
        mock_wb.__exit__ = MagicMock(return_value=False)
        mock_wb[sheet_name] = mock_ws
        mock_load_wb.return_value = mock_wb

        handler = XlsxHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.xlsx",
            sheet_name=sheet_name,
            limit=1
        )
        assert len(result) == 1

    @patch("dal.xlsx_handler.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_cols_allowlist(self, mock_exists, mock_load_wb):
        """Cols parameter acts as allowlist - only specified columns included."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ["name", "age", "email"],
            ["Alice", 30, "alice@test.com"]
        ]
        mock_wb = MagicMock()
        mock_wb.__enter__ = MagicMock(return_value=mock_wb)
        mock_wb.__exit__ = MagicMock(return_value=False)
        mock_wb[sheet_name] = mock_ws
        mock_load_wb.return_value = mock_wb

        handler = XlsxHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.xlsx",
            sheet_name=sheet_name,
            cols=["name", "age"]
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("dal.xlsx_handler.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_custom_header_row(self, mock_exists, mock_load_wb):
        """Custom header_row is used for reading column names."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ["name", "age"],  # Row 0 (ignored)
            ["Alice", 30],    # Row 1 (used as header)
            ["Bob", 25]       # Row 2 (data)
        ]
        mock_wb = MagicMock()
        mock_wb.__enter__ = MagicMock(return_value=mock_wb)
        mock_wb.__exit__ = MagicMock(return_value=False)
        mock_wb[sheet_name] = mock_ws
        mock_load_wb.return_value = mock_wb

        handler = XlsxHandler(header_row=1)
        result = handler.fetch(
            path=Path("data"),
            table="users.xlsx",
            sheet_name=sheet_name
        )
        assert len(result) == 1
        assert "Alice" in str(result)


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

    @patch("dal.xlsx_handler.Workbook")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_all_data(self, mock_exists, mock_mkdir, mock_wb_class):
        """Store writes all data when no filters specified."""
        handler = XlsxHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.xlsx"
        )
        assert result == 1

    @patch("dal.xlsx_handler.Workbook")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_cols_allowlist(self, mock_exists, mock_mkdir, mock_wb_class):
        """Cols parameter acts as allowlist - only specified columns stored."""
        handler = XlsxHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30, "email": "alice@test.com"}],
            path=Path("output"),
            table="users.xlsx",
            cols=["name", "age"]
        )
        assert result == 1

    @patch("dal.xlsx_handler.Workbook")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_filter(self, mock_exists, mock_mkdir, mock_wb_class):
        """Filter is applied before storing."""
        handler = XlsxHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.xlsx",
            filter_=lambda row: row["age"] > 25
        )
        assert result == 1

    @patch("dal.xlsx_handler.Workbook")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_limit(self, mock_exists, mock_mkdir, mock_wb_class):
        """Limit is applied after filtering."""
        handler = XlsxHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.xlsx",
            limit=1
        )
        assert result == 1

    @patch("dal.xlsx_handler.Workbook")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_custom_sheet_name(self, mock_exists, mock_mkdir, mock_wb_class):
        """Custom sheet_name is used when creating workbook."""
        handler = XlsxHandler(sheet_name="CustomSheet")
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.xlsx"
        )
        assert result == 1
