# tests/unit/test_json_handler.py
from pathlib import Path
from unittest.mock import mock_open, patch
import pytest

from data_access_layer.json_handler import JsonHandler


class TestJsonHandlerFetch:
    """Unit tests for JsonHandler.fetch() method."""

    def test_fetch_returns_empty_list_when_strict_false_and_file_not_found(self):
        """When strict=False and file not found, return empty list."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("nonexistent"),
            table="data.json",
            strict=False
        )
        assert result == []

    def test_fetch_raises_file_not_found_when_strict_true(self):
        """When strict=True and file not found, raise FileNotFoundError."""
        handler = JsonHandler()
        with pytest.raises(FileNotFoundError):
            handler.fetch(
                path=Path("nonexistent"),
                table="data.json",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "Alice", "age": 30}]')
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_all_data(self, mock_exists, mock_file):
        """Fetch returns all data when no filters specified."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.json"
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]')
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter(self, mock_exists, mock_file):
        """Filter is applied to rows before returning."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.json",
            filter_=lambda row: row["age"] > 25
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]')
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_limit(self, mock_exists, mock_file):
        """Limit is applied after filtering."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.json",
            limit=1
        )
        assert len(result) == 1
        assert result[0] == {"name": "Alice", "age": 30}

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "Alice", "age": 30, "email": "alice@test.com"}]')
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_cols_allowlist(self, mock_exists, mock_file):
        """Cols parameter acts as allowlist - only specified columns included."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.json",
            cols=["name", "age"]
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]')
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter_and_limit(self, mock_exists, mock_file):
        """Filter is applied first, then limit to filtered results."""
        handler = JsonHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.json",
            filter_=lambda row: row["age"] > 20,
            limit=1
        )
        # Both rows match filter, but only 1 returned due to limit
        assert len(result) == 1


class TestJsonHandlerStore:
    """Unit tests for JsonHandler.store() method."""

    def test_store_returns_zero_when_strict_false_and_path_not_found(self):
        """When strict=False and path doesn't exist, return 0."""
        handler = JsonHandler()
        result = handler.store(
            data=[{"name": "Alice"}],
            path=Path("nonexistent"),
            table="output.json",
            strict=False
        )
        assert result == 0

    def test_store_raises_file_not_found_when_strict_true(self):
        """When strict=True and path doesn't exist, raise FileNotFoundError."""
        handler = JsonHandler()
        with pytest.raises(FileNotFoundError):
            handler.store(
                data=[{"name": "Alice"}],
                path=Path("nonexistent"),
                table="output.json",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_all_data(self, mock_exists, mock_mkdir, mock_file):
        """Store writes all data when no filters specified."""
        handler = JsonHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.json"
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_cols_allowlist(self, mock_exists, mock_mkdir, mock_file):
        """Cols parameter acts as allowlist - only specified columns stored."""
        handler = JsonHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30, "email": "alice@test.com"}],
            path=Path("output"),
            table="users.json",
            cols=["name", "age"]
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_filter(self, mock_exists, mock_mkdir, mock_file):
        """Filter is applied before storing."""
        handler = JsonHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.json",
            filter_=lambda row: row["age"] > 25
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_limit(self, mock_exists, mock_mkdir, mock_file):
        """Limit is applied after filtering."""
        handler = JsonHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.json",
            limit=1
        )
        assert result == 1
