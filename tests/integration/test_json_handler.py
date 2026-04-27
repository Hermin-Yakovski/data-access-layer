from pathlib import Path
import json
import pytest

from dal import JsonHandler


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


class TestJsonHandlerFetchIntegration:
    """Integration tests for JsonHandler.fetch() with real files."""

    def test_fetch_from_real_json_file(self, temp_dir):
        """Fetch data from an actual JSON file."""
        # Create test data file
        test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        test_file = temp_dir / "users.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        # Fetch and verify
        handler = JsonHandler()
        result = handler.fetch(path=temp_dir, table="users.json")
        assert result == test_data

    def test_fetch_with_encoding(self, temp_dir):
        """Fetch JSON file with different encoding."""
        test_data = [{"name": "Müller", "city": "Zürich"}]
        test_file = temp_dir / "users.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)

        handler = JsonHandler(encoding='utf-8')
        result = handler.fetch(path=temp_dir, table="users.json")
        assert result == test_data

    def test_fetch_empty_file(self, temp_dir):
        """Fetch from an empty JSON array file."""
        test_file = temp_dir / "empty.json"
        with open(test_file, 'w') as f:
            json.dump([], f)

        handler = JsonHandler()
        result = handler.fetch(path=temp_dir, table="empty.json")
        assert result == []

    def test_fetch_invalid_json_raises_value_error(self, temp_dir):
        """Fetching invalid JSON raises ValueError when strict=True."""
        test_file = temp_dir / "invalid.json"
        with open(test_file, 'w') as f:
            f.write('{"invalid": json}');

        handler = JsonHandler()
        with pytest.raises(ValueError):
            handler.fetch(path=temp_dir, table="invalid.json", strict=True)


class TestJsonHandlerStoreIntegration:
    """Integration tests for JsonHandler.store() with real files."""

    def test_store_to_real_json_file(self, temp_dir):
        """Store data to an actual JSON file."""
        test_data = [{"name": "Alice", "age": 30}]
        handler = JsonHandler()

        result = handler.store(
            data=test_data,
            path=temp_dir,
            table="users.json"
        )
        assert result == 1

        # Verify file was written correctly
        test_file = temp_dir / "users.json"
        with open(test_file, 'r') as f:
            stored_data = json.load(f)
        assert stored_data == test_data

    def test_store_with_indent(self, temp_dir):
        """Store with custom indentation."""
        test_data = [{"name": "Alice"}]
        handler = JsonHandler(indent=4)

        handler.store(data=test_data, path=temp_dir, table="users.json")

        # Verify indentation
        test_file = temp_dir / "users.json"
        content = test_file.read_text()
        assert "    " in content  # 4 spaces

    def test_store_overwrite_replaces_file(self, temp_dir):
        """Store with overwrite=True replaces existing file."""
        # Create initial file
        initial_data = [{"name": "Alice"}]
        test_file = temp_dir / "users.json"
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)

        # Store new data with overwrite=True
        new_data = [{"name": "Bob"}]
        handler = JsonHandler()
        handler.store(data=new_data, path=temp_dir, table="users.json", overwrite=True)

        # Verify file was replaced
        with open(test_file, 'r') as f:
            stored_data = json.load(f)
        assert stored_data == new_data

    def test_store_append_adds_to_existing(self, temp_dir):
        """Store with overwrite=False appends to existing data."""
        # Create initial file
        initial_data = [{"name": "Alice"}]
        test_file = temp_dir / "users.json"
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)

        # Store new data with overwrite=False
        new_data = [{"name": "Bob"}]
        handler = JsonHandler()
        handler.store(data=new_data, path=temp_dir, table="users.json", overwrite=False)

        # Verify data was appended
        with open(test_file, 'r') as f:
            stored_data = json.load(f)
        assert stored_data == initial_data + new_data
