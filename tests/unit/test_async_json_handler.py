import pytest
from pathlib import Path
from dal.json_handler import AsyncJsonHandler

@pytest.mark.asyncio
async def test_async_json_fetch_basic(tmp_path):
    """Test basic async fetch from JSON file."""
    import json
    test_file = tmp_path / "test.json"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_text(json.dumps(test_data))

    handler = AsyncJsonHandler()
    result = await handler.fetch(tmp_path, "test.json")

    assert result == test_data

@pytest.mark.asyncio
async def test_async_json_fetch_with_filter(tmp_path):
    """Test async fetch with filter."""
    import json
    test_file = tmp_path / "test.json"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_text(json.dumps(test_data))

    handler = AsyncJsonHandler()
    result = await handler.fetch(
        tmp_path, "test.json",
        filter_=lambda row: row["age"] > 25
    )

    assert len(result) == 1
    assert result[0]["name"] == "Alice"

@pytest.mark.asyncio
async def test_async_json_fetch_strict_false_missing_file(tmp_path):
    """Test lenient mode returns empty list for missing file."""
    handler = AsyncJsonHandler()
    result = await handler.fetch(tmp_path, "missing.json", strict=False)

    assert result == []

@pytest.mark.asyncio
async def test_async_json_store_basic(tmp_path):
    """Test basic async store to JSON file."""
    import json
    test_file = tmp_path / "test.json"
    test_data = [{"name": "Charlie", "age": 35}]

    handler = AsyncJsonHandler()
    count = await handler.store(test_data, tmp_path, "test.json")

    assert count == 1
    result = json.loads(test_file.read_text())
    assert result == test_data

@pytest.mark.asyncio
async def test_async_json_store_append_mode(tmp_path):
    """Test append mode doesn't overwrite existing data."""
    import json
    test_file = tmp_path / "test.json"
    existing_data = [{"name": "David", "age": 40}]
    new_data = [{"name": "Eve", "age": 28}]

    handler = AsyncJsonHandler()

    # Store initial data
    await handler.store(existing_data, tmp_path, "test.json")

    # Append new data
    await handler.store(new_data, tmp_path, "test.json", overwrite=False)

    # Verify both datasets exist
    result = json.loads(test_file.read_text())
    assert len(result) == 2
    assert result[0]["name"] == "David"
    assert result[1]["name"] == "Eve"
