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

    def test_fetch_dict_not_list_raises_value_error(self, temp_dir):
        """Fetching JSON dict object (not list) raises ValueError."""
        test_file = temp_dir / "dict.json"
        with open(test_file, 'w') as f:
            json.dump({"name": "Alice"}, f)

        handler = JsonHandler()
        with pytest.raises(ValueError, match="must contain a list.*got dict"):
            handler.fetch(path=temp_dir, table="dict.json", strict=True)

    def test_fetch_string_not_list_raises_value_error(self, temp_dir):
        """Fetching JSON string (not list) raises ValueError."""
        test_file = temp_dir / "string.json"
        with open(test_file, 'w') as f:
            json.dump("just a string", f)

        handler = JsonHandler()
        with pytest.raises(ValueError, match="must contain a list.*got str"):
            handler.fetch(path=temp_dir, table="string.json", strict=True)

    def test_fetch_dict_not_list_strict_false(self, temp_dir):
        """Fetching JSON dict object returns empty list in lenient mode."""
        test_file = temp_dir / "dict.json"
        with open(test_file, 'w') as f:
            json.dump({"name": "Alice"}, f)

        handler = JsonHandler()
        result = handler.fetch(path=temp_dir, table="dict.json", strict=False)
        assert result == []

    def test_fetch_nonexistent_directory_raises_file_not_found(self, temp_dir):
        """Fetching from non-existent directory raises FileNotFoundError."""
        nonexistent_dir = temp_dir / "nonexistent"
        handler = JsonHandler()

        with pytest.raises(FileNotFoundError, match="Directory.*does not exist"):
            handler.fetch(path=nonexistent_dir, table="users.json", strict=True)

    def test_fetch_nonexistent_directory_strict_false(self, temp_dir):
        """Fetching from non-existent directory returns empty list in lenient mode."""
        nonexistent_dir = temp_dir / "nonexistent"
        handler = JsonHandler()

        result = handler.fetch(path=nonexistent_dir, table="users.json", strict=False)
        assert result == []

    def test_fetch_nonexistent_file_raises_file_not_found(self, temp_dir):
        """Fetching non-existent file raises FileNotFoundError."""
        handler = JsonHandler()

        with pytest.raises(FileNotFoundError, match="File.*not found"):
            handler.fetch(path=temp_dir, table="nonexistent.json", strict=True)

    def test_fetch_nonexistent_file_strict_false(self, temp_dir):
        """Fetching non-existent file returns empty list in lenient mode."""
        handler = JsonHandler()

        result = handler.fetch(path=temp_dir, table="nonexistent.json", strict=False)
        assert result == []


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

    def test_fetch_with_non_dict_items_raises_value_error(self, temp_dir):
        """Fetching JSON with non-dict items raises ValueError."""
        test_file = temp_dir / "invalid.json"
        # Create JSON with a list containing a string instead of dict
        with open(test_file, 'w') as f:
            json.dump([{"name": "Alice"}, "not_a_dict", {"name": "Bob"}], f)

        handler = JsonHandler()
        with pytest.raises(ValueError, match="item at index 1 is str"):
            handler.fetch(path=temp_dir, table="invalid.json", strict=True)

    def test_fetch_with_non_dict_items_strict_false(self, temp_dir):
        """Fetching JSON with non-dict items returns empty list in lenient mode."""
        test_file = temp_dir / "invalid.json"
        with open(test_file, 'w') as f:
            json.dump([{"name": "Alice"}, "not_a_dict"], f)

        handler = JsonHandler()
        result = handler.fetch(path=temp_dir, table="invalid.json", strict=False)
        assert result == []

    def test_fetch_with_list_of_lists_raises_value_error(self, temp_dir):
        """Fetching JSON that is a list of lists instead of list of dicts raises ValueError."""
        test_file = temp_dir / "invalid.json"
        with open(test_file, 'w') as f:
            json.dump([["Alice", 30], ["Bob", 25]], f)

        handler = JsonHandler()
        with pytest.raises(ValueError, match="item at index 0 is list"):
            handler.fetch(path=temp_dir, table="invalid.json", strict=True)


class TestJsonHandlerTypeCoercion:
    """Integration tests for JsonHandler type coercion feature."""

    def test_fetch_with_types_coerces_strings_to_int(self, temp_dir):
        """Type coercion converts string fields to specified types."""
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30'}],
            path=temp_dir,
            table='test_types.json'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types.json',
            types={'id': int, 'age': int}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)
        assert result[0]['name'] == 'Alice'  # unchanged

    def test_fetch_with_types_and_cols(self, temp_dir):
        """Type coercion works with column selection."""
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30', 'active': 'true'}],
            path=temp_dir,
            table='test_types_cols.json'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types_cols.json',
            types={'id': int, 'age': int, 'active': bool},
            cols=['id', 'age', 'active']
        )

        assert result == [{'id': 1, 'age': 30, 'active': True}]
        assert isinstance(result[0]['active'], bool)

    def test_fetch_with_types_and_filter(self, temp_dir):
        """Type coercion happens before filter is applied."""
        handler = JsonHandler()
        handler.store(
            [
                {'id': '1', 'age': '30'},
                {'id': '2', 'age': '25'},
                {'id': '3', 'age': '35'}
            ],
            path=temp_dir,
            table='test_types_filter.json'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types_filter.json',
            types={'age': int},
            filter_=lambda r: r['age'] > 28
        )

        assert len(result) == 2
        assert result[0]['id'] == '1'
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)

    def test_fetch_with_types_coercion_failure_raises_typeerror(self, temp_dir):
        """Type coercion failure raises descriptive TypeError."""
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'age': 'not_a_number'}],
            path=temp_dir,
            table='test_types_error.json'
        )

        with pytest.raises(TypeError, match="Failed to coerce field 'age'"):
            handler.fetch(
                path=temp_dir,
                table='test_types_error.json',
                types={'age': int}
            )

    def test_store_with_types_coerces_before_writing(self, temp_dir):
        """Store coerces types before writing to file."""
        handler = JsonHandler()
        handler.store(
            [{'id': 1, 'name': 'Alice', 'age': 30}],  # ints
            path=temp_dir,
            table='test_store_types.json',
            types={'id': str, 'name': str, 'age': str}  # coerce to strings
        )

        # Read back without coercion to verify stored as strings
        result = handler.fetch(path=temp_dir, table='test_store_types.json')

        assert result[0]['id'] == '1'
        assert isinstance(result[0]['id'], str)
        assert result[0]['age'] == '30'
        assert isinstance(result[0]['age'], str)
