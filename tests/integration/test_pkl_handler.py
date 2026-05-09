from pathlib import Path
import pickle
import pytest

from dal import PklHandler


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


class TestPklHandlerFetchIntegration:
    """Integration tests for PklHandler.fetch() with real files."""

    def test_fetch_from_real_pkl_file(self, temp_dir):
        """Fetch data from an actual pickle file."""
        # Create test data file
        test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(test_data, f)

        # Fetch and verify
        handler = PklHandler()
        result = handler.fetch(path=temp_dir, table="users.pkl")
        assert result == test_data

    def test_fetch_empty_file(self, temp_dir):
        """Fetch from an empty pickle file."""
        test_data = []
        test_file = temp_dir / "empty.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(test_data, f)

        handler = PklHandler()
        result = handler.fetch(path=temp_dir, table="empty.pkl")
        assert result == []

    def test_fetch_with_protocol(self, temp_dir):
        """Fetch pickle file with specific protocol."""
        test_data = [{"name": "Alice", "age": 30}]
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(test_data, f, protocol=4)

        handler = PklHandler(protocol=4)
        result = handler.fetch(path=temp_dir, table="users.pkl")
        assert result == test_data


class TestPklHandlerStoreIntegration:
    """Integration tests for PklHandler.store() with real files."""

    def test_store_to_real_pkl_file(self, temp_dir):
        """Store data to an actual pickle file."""
        test_data = [{"name": "Alice", "age": 30}]
        handler = PklHandler()

        result = handler.store(
            data=test_data,
            path=temp_dir,
            table="users.pkl"
        )
        assert result == 1

        # Verify file was written correctly
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == test_data

    def test_store_with_protocol(self, temp_dir):
        """Store with custom protocol."""
        test_data = [{"name": "Alice", "age": 30}]
        handler = PklHandler(protocol=4)

        handler.store(data=test_data, path=temp_dir, table="users.pkl")

        # Verify protocol can be read back
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == test_data

    def test_store_overwrite_replaces_file(self, temp_dir):
        """Store with overwrite=True replaces existing file."""
        # Create initial file
        initial_data = [{"name": "Alice"}]
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(initial_data, f)

        # Store new data with overwrite=True
        new_data = [{"name": "Bob"}]
        handler = PklHandler()
        handler.store(data=new_data, path=temp_dir, table="users.pkl", overwrite=True)

        # Verify file was replaced
        with open(test_file, 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == new_data

    def test_store_append_adds_to_existing(self, temp_dir):
        """Store with overwrite=False appends to existing data."""
        # Create initial file
        initial_data = [{"name": "Alice"}]
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(initial_data, f)

        # Store new data with overwrite=False
        new_data = [{"name": "Bob"}]
        handler = PklHandler()
        handler.store(data=new_data, path=temp_dir, table="users.pkl", overwrite=False)

        # Verify data was appended
        with open(test_file, 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == initial_data + new_data

    def test_store_with_filter(self, temp_dir):
        """Store applies filter before writing."""
        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        handler = PklHandler()

        handler.store(
            data=test_data,
            path=temp_dir,
            table="users.pkl",
            filter_=lambda row: row["age"] > 25
        )

        # Verify only Alice was stored
        test_file = temp_dir / "users.pkl"
        with open(test_file, 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == [{"name": "Alice", "age": 30}]

    def test_fetch_with_non_dict_items_raises_value_error(self, temp_dir):
        """Fetching pickle with non-dict items raises ValueError."""
        import pickle

        test_file = temp_dir / "invalid.pkl"
        # Create pickle with a list containing a string instead of dict
        with open(test_file, 'wb') as f:
            pickle.dump([{"name": "Alice"}, "not_a_dict", {"name": "Bob"}], f)

        handler = PklHandler()
        with pytest.raises(ValueError, match="item at index 1 is str"):
            handler.fetch(path=temp_dir, table="invalid.pkl", strict=True)

    def test_fetch_with_non_dict_items_strict_false(self, temp_dir):
        """Fetching pickle with non-dict items returns empty list in lenient mode."""
        import pickle

        test_file = temp_dir / "invalid.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump([{"name": "Alice"}, "not_a_dict"], f)

        handler = PklHandler()
        result = handler.fetch(path=temp_dir, table="invalid.pkl", strict=False)
        assert result == []

    def test_fetch_with_list_of_lists_raises_value_error(self, temp_dir):
        """Fetching pickle that is a list of lists instead of list of dicts raises ValueError."""
        import pickle

        test_file = temp_dir / "invalid.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump([["Alice", 30], ["Bob", 25]], f)

        handler = PklHandler()
        with pytest.raises(ValueError, match="item at index 0 is list"):
            handler.fetch(path=temp_dir, table="invalid.pkl", strict=True)


class TestPklHandlerTypeCoercion:
    """Integration tests for PklHandler type coercion with real files."""

    def test_fetch_with_types_coerces_values(self, temp_dir):
        """Fetch with types parameter coerces string values to specified types."""
        handler = PklHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'active': 'true'}],
            path=temp_dir,
            table='test_types.pkl'
        )

        result = handler.fetch(
            path=temp_dir,
            table='test_types.pkl',
            types={'id': int, 'active': bool}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['active'] is True
        assert isinstance(result[0]['active'], bool)
