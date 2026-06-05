# tests/unit/test_pkl_handler.py
from pathlib import Path
from unittest.mock import mock_open, patch
import pickle
import pytest

from data_access_layer.pkl_handler import PklHandler


class TestPklHandlerFetch:
    """Unit tests for PklHandler.fetch() method."""

    def test_fetch_returns_empty_list_when_strict_false_and_file_not_found(self):
        """When strict=False and file not found, return empty list."""
        handler = PklHandler()
        result = handler.fetch(
            path=Path("nonexistent"),
            table="data.pkl",
            strict=False
        )
        assert result == []

    def test_fetch_raises_file_not_found_when_strict_true(self):
        """When strict=True and file not found, raise FileNotFoundError."""
        handler = PklHandler()
        with pytest.raises(FileNotFoundError):
            handler.fetch(
                path=Path("nonexistent"),
                table="data.pkl",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_all_data(self, mock_exists, mock_file):
        """Fetch returns all data when no filters specified."""
        test_data = [{"name": "Alice", "age": 30}]
        mock_file.return_value.read.return_value = pickle.dumps(test_data)

        handler = PklHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.pkl"
        )
        assert result == test_data

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter(self, mock_exists, mock_file):
        """Filter is applied to rows before returning."""
        test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        mock_file.return_value.read.return_value = pickle.dumps(test_data)

        handler = PklHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.pkl",
            filter_=lambda row: row["age"] > 25
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_limit(self, mock_exists, mock_file):
        """Limit is applied after filtering."""
        test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        mock_file.return_value.read.return_value = pickle.dumps(test_data)

        handler = PklHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.pkl",
            limit=1
        )
        assert len(result) == 1
        assert result[0] == {"name": "Alice", "age": 30}

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_cols_allowlist(self, mock_exists, mock_file):
        """Cols parameter acts as allowlist - only specified columns included."""
        test_data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        mock_file.return_value.read.return_value = pickle.dumps(test_data)

        handler = PklHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.pkl",
            cols=["name", "age"]
        )
        assert result == [{"name": "Alice", "age": 30}]

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_protocol(self, mock_exists, mock_file):
        """Custom protocol is used for unpickling."""
        test_data = [{"name": "Alice", "age": 30}]
        mock_file.return_value.read.return_value = pickle.dumps(test_data, protocol=4)

        handler = PklHandler(protocol=4)
        result = handler.fetch(
            path=Path("data"),
            table="users.pkl"
        )
        assert result == test_data


class TestPklHandlerStore:
    """Unit tests for PklHandler.store() method."""

    def test_store_returns_zero_when_strict_false_and_path_not_found(self):
        """When strict=False and path doesn't exist, return 0."""
        handler = PklHandler()
        result = handler.store(
            data=[{"name": "Alice"}],
            path=Path("nonexistent"),
            table="output.pkl",
            strict=False
        )
        assert result == 0

    def test_store_raises_file_not_found_when_strict_true(self):
        """When strict=True and path doesn't exist, raise FileNotFoundError."""
        handler = PklHandler()
        with pytest.raises(FileNotFoundError):
            handler.store(
                data=[{"name": "Alice"}],
                path=Path("nonexistent"),
                table="output.pkl",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_all_data(self, mock_exists, mock_mkdir, mock_file):
        """Store writes all data when no filters specified."""
        handler = PklHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.pkl"
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_cols_allowlist(self, mock_exists, mock_mkdir, mock_file):
        """Cols parameter acts as allowlist - only specified columns stored."""
        handler = PklHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30, "email": "alice@test.com"}],
            path=Path("output"),
            table="users.pkl",
            cols=["name", "age"]
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_filter(self, mock_exists, mock_mkdir, mock_file):
        """Filter is applied before storing."""
        handler = PklHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.pkl",
            filter_=lambda row: row["age"] > 25
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_limit(self, mock_exists, mock_mkdir, mock_file):
        """Limit is applied after filtering."""
        handler = PklHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.pkl",
            limit=1
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_protocol(self, mock_exists, mock_mkdir, mock_file):
        """Custom protocol is used for pickling."""
        handler = PklHandler(protocol=4)
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.pkl"
        )
        assert result == 1
