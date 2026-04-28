from pathlib import Path
import pytest

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

if HAS_OPENPYXL:
    from dal import XlsxHandler


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerFetchIntegration:
    """Integration tests for XlsxHandler.fetch() with real files."""

    def test_fetch_from_real_xlsx_file(self, temp_dir):
        """Fetch data from an actual XLSX file."""
        from openpyxl import Workbook

        # Create test data file
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        ws.append(["Bob", 25])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        # Fetch and verify
        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="users.xlsx")
        assert result == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    def test_fetch_empty_file(self, temp_dir):
        """Fetch from an XLSX file with header only."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])

        test_file = temp_dir / "empty.xlsx"
        wb.save(test_file)

        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="empty.xlsx")
        assert result == []

    def test_fetch_with_custom_sheet_name(self, temp_dir):
        """Fetch XLSX file with custom sheet name."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "CustomSheet"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])

        test_file = temp_dir / "data.xlsx"
        wb.save(test_file)

        handler = XlsxHandler(sheet_name="CustomSheet")
        result = handler.fetch(path=temp_dir, table="data.xlsx")
        assert result == [{"name": "Alice", "age": 30}]

    def test_fetch_with_column_selection(self, temp_dir):
        """Fetch with column allowlist - only specified columns included."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age", "email"])
        ws.append(["Alice", 30, "alice@test.com"])
        ws.append(["Bob", 25, "bob@test.com"])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="users.xlsx", cols=["name", "age"])
        assert result == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    def test_fetch_with_filter(self, temp_dir):
        """Filter is applied to rows."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        ws.append(["Bob", 25])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="users.xlsx", filter_=lambda row: row["age"] > 25)
        assert result == [{"name": "Alice", "age": 30}]

    def test_fetch_with_limit(self, temp_dir):
        """Limit is applied after filtering."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        ws.append(["Bob", 25])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="users.xlsx", limit=1)
        assert len(result) == 1
        assert result[0] == {"name": "Alice", "age": 30}

    def test_fetch_with_filter_and_limit(self, temp_dir):
        """Filter is applied first, then limit to filtered results."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        ws.append(["Bob", 25])
        ws.append(["Charlie", 35])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler()
        result = handler.fetch(
            path=temp_dir, table="users.xlsx", filter_=lambda row: row["age"] >= 30, limit=1
        )
        # Two rows match filter (Alice 30, Charlie 35), but only 1 returned due to limit
        assert len(result) == 1

    def test_fetch_with_header_row_not_found_raises_value_error(self, temp_dir):
        """Fetching when header row is out of range raises ValueError."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        # Only add one row (header should be at row 0, but we set header_row to 5)
        ws.append(["name", "age"])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler(header_row=5)
        with pytest.raises(ValueError, match="Header row 5 not found"):
            handler.fetch(path=temp_dir, table="users.xlsx", strict=True)

    def test_fetch_with_header_row_not_found_strict_false(self, temp_dir):
        """Fetching when header row is out of range returns empty list in lenient mode."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        # Only add one row (header should be at row 0, but we set header_row to 5)
        ws.append(["name", "age"])

        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        handler = XlsxHandler(header_row=5)
        result = handler.fetch(path=temp_dir, table="users.xlsx", strict=False)
        assert result == []

    def test_fetch_file_not_found_when_directory_exists(self, temp_dir):
        """Fetching when directory exists but file doesn't exist raises FileNotFoundError."""
        handler = XlsxHandler()
        with pytest.raises(FileNotFoundError, match="not found"):
            handler.fetch(path=temp_dir, table="missing.xlsx", strict=True)

    def test_fetch_file_not_found_strict_false(self, temp_dir):
        """Fetching when file doesn't exist returns empty list in lenient mode."""
        handler = XlsxHandler()
        result = handler.fetch(path=temp_dir, table="missing.xlsx", strict=False)
        assert result == []


@pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl not installed")
class TestXlsxHandlerStoreIntegration:
    """Integration tests for XlsxHandler.store() with real files."""

    def test_store_to_real_xlsx_file(self, temp_dir):
        """Store data to an actual XLSX file."""
        from openpyxl import load_workbook

        test_data = [{"name": "Alice", "age": 30}]
        handler = XlsxHandler()

        result = handler.store(
            data=test_data,
            path=temp_dir,
            table="users.xlsx"
        )
        assert result == 1

        # Verify file was written correctly
        test_file = temp_dir / "users.xlsx"
        wb = load_workbook(test_file)
        ws = wb.active
        assert ws["A1"].value == "name"
        assert ws["B1"].value == "age"
        assert ws["A2"].value == "Alice"
        assert ws["B2"].value == 30

    def test_store_with_custom_sheet_name(self, temp_dir):
        """Store with custom sheet name."""
        from openpyxl import load_workbook

        test_data = [{"name": "Alice", "age": 30}]
        handler = XlsxHandler(sheet_name="CustomSheet")

        handler.store(data=test_data, path=temp_dir, table="users.xlsx")

        # Verify sheet name
        test_file = temp_dir / "users.xlsx"
        wb = load_workbook(test_file)
        assert "CustomSheet" in wb.sheetnames

    def test_store_overwrite_replaces_file(self, temp_dir):
        """Store with overwrite=True replaces existing file."""
        from openpyxl import Workbook, load_workbook

        # Create initial file
        wb = Workbook()
        ws = wb.active
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        # Store new data with overwrite=True
        new_data = [{"name": "Bob", "age": 25}]
        handler = XlsxHandler()
        handler.store(data=new_data, path=temp_dir, table="users.xlsx", overwrite=True)

        # Verify file was replaced
        wb = load_workbook(test_file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("name", "age")
        assert rows[1] == ("Bob", 25)

    def test_store_append_adds_to_existing(self, temp_dir):
        """Store with overwrite=False appends to existing data."""
        from openpyxl import Workbook, load_workbook

        # Create initial file
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age"])
        ws.append(["Alice", 30])
        test_file = temp_dir / "users.xlsx"
        wb.save(test_file)

        # Store new data with overwrite=False
        new_data = [{"name": "Bob", "age": 25}]
        handler = XlsxHandler()
        handler.store(data=new_data, path=temp_dir, table="users.xlsx", overwrite=False)

        # Verify data was appended
        wb = load_workbook(test_file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("name", "age")
        assert rows[1] == ("Alice", 30)
        assert rows[2] == ("Bob", 25)

    def test_store_with_column_selection(self, temp_dir):
        """Store with column allowlist - only specified columns stored."""
        from openpyxl import load_workbook

        test_data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        handler = XlsxHandler()

        handler.store(data=test_data, path=temp_dir, table="users.xlsx", cols=["name", "age"])

        # Verify only specified columns stored
        test_file = temp_dir / "users.xlsx"
        wb = load_workbook(test_file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("name", "age")
        assert rows[1] == ("Alice", 30)
        assert len(rows) == 2

    def test_store_with_filter(self, temp_dir):
        """Filter is applied before storing."""
        from openpyxl import load_workbook

        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        handler = XlsxHandler()

        handler.store(data=test_data, path=temp_dir, table="users.xlsx", filter_=lambda row: row["age"] > 25)

        # Verify only filtered data stored
        test_file = temp_dir / "users.xlsx"
        wb = load_workbook(test_file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("name", "age")
        assert rows[1] == ("Alice", 30)
        assert len(rows) == 2

    def test_store_with_limit(self, temp_dir):
        """Limit is applied after filtering."""
        from openpyxl import load_workbook

        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        handler = XlsxHandler()

        handler.store(data=test_data, path=temp_dir, table="users.xlsx", limit=1)

        # Verify only 1 row stored
        test_file = temp_dir / "users.xlsx"
        wb = load_workbook(test_file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("name", "age")
        assert rows[1] == ("Alice", 30)
        assert len(rows) == 2
