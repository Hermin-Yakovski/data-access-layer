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
