import pytest
from pathlib import Path
from dal.csv_handler import AsyncCsvHandler

@pytest.mark.asyncio
async def test_async_csv_fetch_basic(tmp_path):
    """Test basic async fetch from CSV file."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,age\nAlice,30\nBob,25\n")

    handler = AsyncCsvHandler()
    result = await handler.fetch(tmp_path, "test.csv")

    assert len(result) == 2
    assert result[0] == {"name": "Alice", "age": "30"}
    assert result[1] == {"name": "Bob", "age": "25"}

@pytest.mark.asyncio
async def test_async_csv_store_basic(tmp_path):
    """Test basic async store to CSV file."""
    handler = AsyncCsvHandler()
    test_data = [{"name": "Charlie", "age": "35"}]
    rows_written = await handler.store(test_data, tmp_path, "output.csv")

    assert rows_written == 1

    # Verify file content
    result_file = tmp_path / "output.csv"
    content = result_file.read_text()
    assert "Charlie" in content

@pytest.mark.asyncio
async def test_async_csv_store_append(tmp_path):
    """Test append mode."""
    handler = AsyncCsvHandler()

    # First write
    await handler.store([{"name": "A", "age": "1"}], tmp_path, "append.csv")

    # Append
    await handler.store([{"name": "B", "age": "2"}], tmp_path, "append.csv", overwrite=False)

    # Verify
    result_file = tmp_path / "append.csv"
    content = result_file.read_text()
    assert "A" in content
    assert "B" in content
