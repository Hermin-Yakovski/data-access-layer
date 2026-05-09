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


class TestCsvHandlerTypeCoercion:
    """Integration tests for CsvHandler type coercion functionality."""

    def test_fetch_with_types_coerces_csv_strings(self, temp_dir):
        """Type coercion converts CSV string values to specified types."""
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30'}],
            path=temp_dir,
            table='test_types.csv'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types.csv',
            types={'id': int, 'age': int}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)
        # name should remain a string
        assert result[0]['name'] == 'Alice'
        assert isinstance(result[0]['name'], str)

    def test_fetch_with_types_and_filter(self, temp_dir):
        """Type coercion works correctly with filter parameter."""
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'age': '30'}, {'id': '2', 'age': '25'}, {'id': '3', 'age': '35'}],
            path=temp_dir,
            table='test_types_filter.csv'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types_filter.csv',
            types={'age': int},
            filter_=lambda r: r['age'] > 28
        )

        assert len(result) == 2
        assert result[0]['age'] == 30
        assert result[1]['age'] == 35
        # Verify coercion happened
        assert all(isinstance(r['age'], int) for r in result)

    def test_fetch_with_types_and_limit(self, temp_dir):
        """Type coercion works correctly with limit parameter."""
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'score': '95'}, {'id': '2', 'score': '87'}, {'id': '3', 'score': '92'}],
            path=temp_dir,
            table='test_types_limit.csv'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types_limit.csv',
            types={'id': int, 'score': int},
            limit=2
        )

        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['score'] == 95
        assert result[1]['id'] == 2
        assert result[1]['score'] == 87
        # Verify coercion happened
        assert all(isinstance(r['id'], int) and isinstance(r['score'], int) for r in result)

    def test_fetch_with_types_partial_coercion(self, temp_dir):
        """Type coercion only converts specified columns, leaving others as strings."""
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30', 'active': 'true'}],
            path=temp_dir,
            table='test_partial.csv'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_partial.csv',
            types={'id': int, 'age': int}
        )

        # Specified columns are coerced
        assert isinstance(result[0]['id'], int)
        assert result[0]['id'] == 1
        assert isinstance(result[0]['age'], int)
        assert result[0]['age'] == 30
        # Unspecified columns remain strings
        assert isinstance(result[0]['name'], str)
        assert result[0]['name'] == 'Alice'
        assert isinstance(result[0]['active'], str)
        assert result[0]['active'] == 'true'
