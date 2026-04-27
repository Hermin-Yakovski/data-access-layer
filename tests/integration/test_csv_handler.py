from pathlib import Path
import pytest

from dal import CsvHandler


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


class TestCsvHandlerFetchIntegration:
    """Integration tests for CsvHandler.fetch() with real files."""

    def test_fetch_from_real_csv_file(self, temp_dir):
        """Fetch data from an actual CSV file."""
        # Create test data file
        test_file = temp_dir / "users.csv"
        test_file.write_text("name,age\nAlice,30\nBob,25")

        # Fetch and verify
        handler = CsvHandler()
        result = handler.fetch(path=temp_dir, table="users.csv")
        assert result == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    def test_fetch_with_encoding(self, temp_dir):
        """Fetch CSV file with different encoding."""
        test_file = temp_dir / "users.csv"
        test_file.write_text("name,city\nMüller,Zürich", encoding='utf-8')

        handler = CsvHandler(encoding='utf-8')
        result = handler.fetch(path=temp_dir, table="users.csv")
        assert result == [{"name": "Müller", "city": "Zürich"}]

    def test_fetch_empty_file(self, temp_dir):
        """Fetch from an empty CSV file (header only)."""
        test_file = temp_dir / "empty.csv"
        test_file.write_text("name,age\n")

        handler = CsvHandler()
        result = handler.fetch(path=temp_dir, table="empty.csv")
        assert result == []

    def test_fetch_with_custom_delimiter(self, temp_dir):
        """Fetch CSV file with custom delimiter."""
        test_file = temp_dir / "data.csv"
        test_file.write_text("name|age\nAlice|30\nBob|25")

        handler = CsvHandler(delimiter='|')
        result = handler.fetch(path=temp_dir, table="data.csv")
        assert result == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]


class TestCsvHandlerStoreIntegration:
    """Integration tests for CsvHandler.store() with real files."""

    def test_store_to_real_csv_file(self, temp_dir):
        """Store data to an actual CSV file."""
        test_data = [{"name": "Alice", "age": 30}]
        handler = CsvHandler()

        result = handler.store(
            data=test_data,
            path=temp_dir,
            table="users.csv"
        )
        assert result == 1

        # Verify file was written correctly
        test_file = temp_dir / "users.csv"
        content = test_file.read_text()
        assert "name,age" in content
        assert "Alice,30" in content

    def test_store_with_custom_delimiter(self, temp_dir):
        """Store with custom delimiter."""
        test_data = [{"name": "Alice", "age": 30}]
        handler = CsvHandler(delimiter='|')

        handler.store(data=test_data, path=temp_dir, table="users.csv")

        # Verify delimiter
        test_file = temp_dir / "users.csv"
        content = test_file.read_text()
        assert "name|age" in content
        assert "Alice|30" in content

    def test_store_overwrite_replaces_file(self, temp_dir):
        """Store with overwrite=True replaces existing file."""
        # Create initial file
        test_file = temp_dir / "users.csv"
        test_file.write_text("name,age\nAlice,30")

        # Store new data with overwrite=True
        new_data = [{"name": "Bob", "age": 25}]
        handler = CsvHandler()
        handler.store(data=new_data, path=temp_dir, table="users.csv", overwrite=True)

        # Verify file was replaced
        content = test_file.read_text()
        assert "Bob,25" in content
        assert "Alice,30" not in content

    def test_store_append_adds_to_existing(self, temp_dir):
        """Store with overwrite=False appends to existing data."""
        # Create initial file
        test_file = temp_dir / "users.csv"
        test_file.write_text("name,age\nAlice,30")

        # Store new data with overwrite=False
        new_data = [{"name": "Bob", "age": 25}]
        handler = CsvHandler()
        handler.store(data=new_data, path=temp_dir, table="users.csv", overwrite=False)

        # Verify data was appended
        content = test_file.read_text()
        assert "Alice,30" in content
        assert "Bob,25" in content

    def test_store_with_filter(self, temp_dir):
        """Store applies filter before writing."""
        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        handler = CsvHandler()

        handler.store(
            data=test_data,
            path=temp_dir,
            table="users.csv",
            filter_=lambda row: row["age"] > 25
        )

        # Verify only Alice was stored
        test_file = temp_dir / "users.csv"
        content = test_file.read_text()
        assert "Alice,30" in content
        assert "Bob,25" not in content
