from pathlib import Path
import pytest
import sqlite3

from dal.sqlite_handler import SqliteHandler


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    return db_path


class TestSqliteHandlerFetchIntegration:
    """Integration tests for SqliteHandler.fetch() with real databases."""

    def test_fetch_raises_error_when_table_missing_strict_true(self, temp_db):
        """When table doesn't exist and strict=True, raise OperationalError with clear message."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler()
        with pytest.raises(Exception):  # sqlite3.OperationalError wrapped
            handler.fetch(path=temp_db, table="nonexistent_table", strict=True)

    def test_fetch_returns_empty_list_when_table_missing_strict_false(self, temp_db):
        """When table doesn't exist and strict=False, return empty list."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="nonexistent_table", strict=False)
        assert result == []

    def test_fetch_from_real_table(self, temp_db):
        """Fetch data from an actual SQLite table."""
        # Create test table with data
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users")
        assert len(result) == 2
        assert {"name": "Alice", "age": 30, "id": 1} in result
        assert {"name": "Bob", "age": 25, "id": 2} in result

    def test_fetch_empty_table(self, temp_db):
        """Fetch from an empty table returns empty list."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users")
        assert result == []

    def test_fetch_with_column_selection(self, temp_db):
        """Fetch with column allowlist - only specified columns included."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.execute("INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@test.com')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", cols=["name", "age"])
        # Only the specified columns are included (id and email are excluded)
        assert result == [{"name": "Alice", "age": 30}]

    def test_fetch_with_filter(self, temp_db):
        """Filter is applied to rows."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", filter_=lambda row: row["age"] > 25)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_fetch_with_limit(self, temp_db):
        """Limit is applied after filtering."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(path=temp_db, table="users", limit=1)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_fetch_with_filter_and_limit(self, temp_db):
        """Filter is applied first, then limit to filtered results."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Charlie', 35)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table="users",
            filter_=lambda row: row["age"] >= 30,
            limit=1
        )
        # Two rows match filter, but only 1 returned due to limit
        assert len(result) == 1


class TestSqliteHandlerStoreIntegration:
    """Integration tests for SqliteHandler.store() with real databases."""

    def test_store_to_real_table(self, temp_db):
        """Store data to an actual SQLite table (table must exist)."""
        # Create table first
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        test_data = [{"name": "Alice", "age": 30}]
        handler = SqliteHandler()
        result = handler.store(data=test_data, path=temp_db, table="users")
        assert result == 1

        # Verify data was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30)]

    def test_store_raises_error_when_table_missing(self, temp_db):
        """Store should raise error when table doesn't exist (user must create schema)."""
        # Create empty database, no table
        conn = sqlite3.connect(temp_db)
        conn.close()

        handler = SqliteHandler()
        data = [{"name": "Alice", "age": 30}]

        with pytest.raises(Exception):  # Table doesn't exist
            handler.store(data=data, path=temp_db, table="users", strict=True)

    def test_store_overwrite_clears_existing_data(self, temp_db):
        """Store with overwrite=True clears existing data before inserting."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()

        # Overwrite with new data
        new_data = [{"name": "Bob", "age": 25}]
        handler.store(data=new_data, path=temp_db, table="users", overwrite=True)

        # Verify only new data exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Bob", 25)]

    def test_store_append_adds_to_existing_data(self, temp_db):
        """Store with overwrite=False appends to existing data."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()

        # Append more data
        more_data = [{"name": "Bob", "age": 25}]
        handler.store(data=more_data, path=temp_db, table="users", overwrite=False)

        # Verify both rows exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30), ("Bob", 25)]

    def test_store_overwrite_on_empty_table(self, temp_db):
        """Store with overwrite=True on empty table works (DELETE is no-op, then inserts)."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        data = [{"name": "Alice", "age": 30}]
        result = handler.store(data=data, path=temp_db, table="users", overwrite=True)

        assert result == 1

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1

    def test_store_ignores_extra_columns_in_data(self, temp_db):
        """Extra columns in data are silently ignored (only insert columns that exist)."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler()
        # Data has 'email' column which doesn't exist in table
        data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        result = handler.store(data=data, path=temp_db, table="users")

        assert result == 1

        # Verify only name and age were stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        assert columns == ["id", "name", "age"]
        assert "email" not in columns

    def test_store_inserts_null_for_missing_columns(self, temp_db):
        """Missing columns in data get NULL inserted."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.close()

        handler = SqliteHandler()
        # Data missing 'age' and 'email'
        data = [{"name": "Alice"}]
        handler.store(data=data, path=temp_db, table="users")

        # Verify NULL for missing columns
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, email FROM users")
        row = cursor.fetchone()
        conn.close()
        assert row == ("Alice", None, None)

    def test_store_with_column_selection(self, temp_db):
        """Store with column allowlist - only specified columns stored."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, email TEXT)")
        conn.close()

        handler = SqliteHandler()
        data = [{"name": "Alice", "age": 30, "email": "alice@test.com"}]
        handler.store(data=data, path=temp_db, table="users", cols=["name", "age"])

        # Verify only name and age were stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, email FROM users")
        row = cursor.fetchone()
        conn.close()
        assert row == ("Alice", 30, None)

    def test_store_with_filter(self, temp_db):
        """Filter is applied before storing."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = handler.store(data=data, path=temp_db, table="users", filter_=lambda row: row["age"] > 25)

        assert result == 1

        # Verify only filtered data was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, age FROM users")
        rows = cursor.fetchall()
        conn.close()
        assert rows == [("Alice", 30)]

    def test_store_with_limit(self, temp_db):
        """Limit is applied after filtering."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.close()

        handler = SqliteHandler()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = handler.store(data=data, path=temp_db, table="users", limit=1)

        assert result == 1

        # Verify only 1 row was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1


class TestSqliteHandlerTypeCoercion:
    """Integration tests for type coercion in SqliteHandler."""

    def test_fetch_with_types_coerces_values(self, temp_db):
        """fetch() with types parameter coerces string values to target types."""
        # Create table and store string data
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test_types (id TEXT, name TEXT, active TEXT)")
        conn.execute("INSERT INTO test_types VALUES ('1', 'Alice', 'true')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table='test_types',
            types={'id': int, 'active': bool}
        )

        assert len(result) == 1
        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['active'] is True
        assert isinstance(result[0]['active'], bool)
        assert result[0]['name'] == 'Alice'  # name not in types, stays as string

    def test_fetch_with_types_coerces_multiple_rows(self, temp_db):
        """Type coercion works correctly across multiple rows."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id TEXT, name TEXT, age TEXT, active TEXT)")
        conn.execute("INSERT INTO users VALUES ('1', 'Alice', '30', 'true')")
        conn.execute("INSERT INTO users VALUES ('2', 'Bob', '25', 'false')")
        conn.execute("INSERT INTO users VALUES ('3', 'Charlie', '35', '1')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table='users',
            types={'id': int, 'age': int, 'active': bool}
        )

        assert len(result) == 3
        assert result[0] == {'id': 1, 'name': 'Alice', 'age': 30, 'active': True}
        assert result[1] == {'id': 2, 'name': 'Bob', 'age': 25, 'active': False}
        assert result[2] == {'id': 3, 'name': 'Charlie', 'age': 35, 'active': True}

    def test_store_with_types_coerces_values(self, temp_db):
        """store() with types parameter coerces values before storing."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test_types (id INTEGER, name TEXT, active INTEGER)")
        conn.close()

        handler = SqliteHandler()
        result = handler.store(
            [{'id': '1', 'name': 'Alice', 'active': 'true'}],
            path=temp_db,
            table='test_types',
            types={'id': int, 'active': bool}
        )

        assert result == 1

        # Verify data was stored with coerced types
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, active FROM test_types")
        row = cursor.fetchone()
        conn.close()

        assert row == (1, 'Alice', 1)  # bool true stored as integer 1

    def test_store_with_types_handles_none_values(self, temp_db):
        """Type coercion handles None values with default values."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER, active INTEGER)")
        conn.close()

        handler = SqliteHandler()
        result = handler.store(
            [{'id': None, 'name': 'Alice', 'age': None, 'active': None}],
            path=temp_db,
            table='users',
            types={'id': int, 'age': int, 'active': bool}
        )

        assert result == 1

        # Verify None values were coerced to defaults
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, active FROM users")
        row = cursor.fetchone()
        conn.close()

        assert row == (0, 'Alice', 0, 0)  # None -> 0 for int, False for bool

    def test_fetch_with_types_float_coercion(self, temp_db):
        """Type coercion works for float types."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE products (id TEXT, name TEXT, price TEXT)")
        conn.execute("INSERT INTO products VALUES ('1', 'Widget', '19.99')")
        conn.execute("INSERT INTO products VALUES ('2', 'Gadget', '29.50')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table='products',
            types={'id': int, 'price': float}
        )

        assert len(result) == 2
        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['price'] == 19.99
        assert isinstance(result[0]['price'], float)
        assert result[1]['price'] == 29.50

    def test_fetch_with_types_bool_string_variations(self, temp_db):
        """Boolean coercion handles various string representations."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE bool_test (id INTEGER, value TEXT)")
        conn.execute("INSERT INTO bool_test VALUES (1, 'true')")
        conn.execute("INSERT INTO bool_test VALUES (2, 'false')")
        conn.execute("INSERT INTO bool_test VALUES (3, '1')")
        conn.execute("INSERT INTO bool_test VALUES (4, '0')")
        conn.execute("INSERT INTO bool_test VALUES (5, 'yes')")
        conn.execute("INSERT INTO bool_test VALUES (6, 'no')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        result = handler.fetch(
            path=temp_db,
            table='bool_test',
            types={'value': bool}
        )

        assert len(result) == 6
        assert result[0]['value'] is True
        assert result[1]['value'] is False
        assert result[2]['value'] is True
        assert result[3]['value'] is False
        assert result[4]['value'] is True
        assert result[5]['value'] is False

    def test_fetch_with_types_invalid_bool_raises_error(self, temp_db):
        """Invalid bool string raises TypeError."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE bool_test (id INTEGER, value TEXT)")
        conn.execute("INSERT INTO bool_test VALUES (1, 'invalid')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        with pytest.raises(TypeError, match="Failed to coerce field 'value'"):
            handler.fetch(
                path=temp_db,
                table='bool_test',
                types={'value': bool}
            )

    def test_fetch_with_types_no_partial_coercion(self, temp_db):
        """When type coercion fails, no rows are returned (transactional behavior)."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE users (id TEXT, name TEXT, age TEXT)")
        conn.execute("INSERT INTO users VALUES ('1', 'Alice', '30')")
        conn.execute("INSERT INTO users VALUES ('2', 'Bob', 'not_a_number')")
        conn.commit()
        conn.close()

        handler = SqliteHandler()
        with pytest.raises(TypeError):
            handler.fetch(
                path=temp_db,
                table='users',
                types={'age': int}
            )
