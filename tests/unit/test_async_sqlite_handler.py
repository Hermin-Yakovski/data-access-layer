import pytest
from pathlib import Path
from data_access_layer.sqlite_handler import AsyncSqliteHandler

@pytest.mark.asyncio
async def test_async_sqlite_fetch_basic(tmp_path):
    """Test basic async fetch from SQLite database."""
    import sqlite3

    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 25)")
    conn.commit()
    conn.close()

    handler = AsyncSqliteHandler()
    result = await handler.fetch(db_file, "users")

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Alice", "age": 30}

@pytest.mark.asyncio
async def test_async_sqlite_store_basic(tmp_path):
    """Test basic async store to SQLite database."""
    import sqlite3

    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
    conn.commit()
    conn.close()

    handler = AsyncSqliteHandler()
    test_data = [{"id": 3, "name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, db_file, "users")

    assert rows_written == 1

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = 3")
    result = cursor.fetchone()
    conn.close()
    assert result == (3, "Charlie", 35)
