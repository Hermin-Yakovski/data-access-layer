# tests/unit/test_csv_handler.py
from pathlib import Path
from unittest.mock import mock_open, patch
import pytest

from dal.csv_handler import CsvHandler


class TestCsvHandlerFetch:
    """Unit tests for CsvHandler.fetch() method."""

    def test_fetch_returns_empty_list_when_strict_false_and_file_not_found(self):
        """When strict=False and file not found, return empty list."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("nonexistent"),
            table="data.csv",
            strict=False
        )
        assert result == []

    def test_fetch_raises_file_not_found_when_strict_true(self):
        """When strict=True and file not found, raise FileNotFoundError."""
        handler = CsvHandler()
        with pytest.raises(FileNotFoundError):
            handler.fetch(
                path=Path("nonexistent"),
                table="data.csv",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open, read_data="name,age\nAlice,30\nBob,25")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_all_data(self, mock_exists, mock_file):
        """Fetch returns all data when no filters specified."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.csv"
        )
        assert result == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    @patch("builtins.open", new_callable=mock_open, read_data="name,age\nAlice,30\nBob,25")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter(self, mock_exists, mock_file):
        """Filter is applied to rows before returning."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.csv",
            filter_=lambda row: int(row["age"]) > 25
        )
        assert result == [{"name": "Alice", "age": "30"}]

    @patch("builtins.open", new_callable=mock_open, read_data="name,age\nAlice,30\nBob,25\nCharlie,35")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_limit(self, mock_exists, mock_file):
        """Limit is applied after filtering."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.csv",
            limit=2
        )
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}

    @patch("builtins.open", new_callable=mock_open, read_data="name,age,email\nAlice,30,alice@test.com")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_cols_allowlist(self, mock_exists, mock_file):
        """Cols parameter acts as allowlist - only specified columns included."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.csv",
            cols=["name", "age"]
        )
        assert result == [{"name": "Alice", "age": "30"}]

    @patch("builtins.open", new_callable=mock_open, read_data="name,age\nAlice,30\nBob,25\nCharlie,35")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_filter_and_limit(self, mock_exists, mock_file):
        """Filter is applied first, then limit to filtered results."""
        handler = CsvHandler()
        result = handler.fetch(
            path=Path("data"),
            table="users.csv",
            filter_=lambda row: int(row["age"]) > 20,
            limit=2
        )
        # All rows match filter, but only 2 returned due to limit
        assert len(result) == 2

    @patch("builtins.open", new_callable=mock_open, read_data="name|age\nAlice|30\nBob|25")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_custom_delimiter(self, mock_exists, mock_file):
        """Custom delimiter is used for parsing CSV."""
        handler = CsvHandler(delimiter='|')
        result = handler.fetch(
            path=Path("data"),
            table="users.csv"
        )
        assert result == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    @patch("builtins.open", new_callable=mock_open, read_data="name,age\nAlice,30")
    @patch("pathlib.Path.exists", return_value=True)
    def test_fetch_with_encoding(self, mock_exists, mock_file):
        """Custom encoding is used for reading file."""
        handler = CsvHandler(encoding='utf-8')
        result = handler.fetch(
            path=Path("data"),
            table="users.csv"
        )
        assert result == [{"name": "Alice", "age": "30"}]


class TestCsvHandlerStore:
    """Unit tests for CsvHandler.store() method."""

    def test_store_returns_zero_when_strict_false_and_path_not_found(self):
        """When strict=False and path doesn't exist, return 0."""
        handler = CsvHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("nonexistent"),
            table="output.csv",
            strict=False
        )
        assert result == 0

    def test_store_raises_file_not_found_when_strict_true(self):
        """When strict=True and path doesn't exist, raise FileNotFoundError."""
        handler = CsvHandler()
        with pytest.raises(FileNotFoundError):
            handler.store(
                data=[{"name": "Alice", "age": 30}],
                path=Path("nonexistent"),
                table="output.csv",
                strict=True
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_all_data(self, mock_exists, mock_mkdir, mock_file):
        """Store writes all data when no filters specified."""
        handler = CsvHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.csv"
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_cols_allowlist(self, mock_exists, mock_mkdir, mock_file):
        """Cols parameter acts as allowlist - only specified columns stored."""
        handler = CsvHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30, "email": "alice@test.com"}],
            path=Path("output"),
            table="users.csv",
            cols=["name", "age"]
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_filter(self, mock_exists, mock_mkdir, mock_file):
        """Filter is applied before storing."""
        handler = CsvHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.csv",
            filter_=lambda row: row["age"] > 25
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_limit(self, mock_exists, mock_mkdir, mock_file):
        """Limit is applied after filtering."""
        handler = CsvHandler()
        result = handler.store(
            data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            path=Path("output"),
            table="users.csv",
            limit=1
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_custom_delimiter(self, mock_exists, mock_mkdir, mock_file):
        """Custom delimiter is used for writing CSV."""
        handler = CsvHandler(delimiter='|')
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.csv"
        )
        assert result == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_store_with_encoding(self, mock_exists, mock_mkdir, mock_file):
        """Custom encoding is used for writing file."""
        handler = CsvHandler(encoding='utf-8')
        result = handler.store(
            data=[{"name": "Alice", "age": 30}],
            path=Path("output"),
            table="users.csv"
        )
        assert result == 1
