import pytest
from pathlib import Path
from data_access_layer.pkl_handler import AsyncPklHandler


@pytest.mark.asyncio
async def test_async_pkl_fetch_basic(tmp_path):
    """Test basic async fetch from pickle file."""
    import pickle
    test_file = tmp_path / "test.pkl"
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    test_file.write_bytes(pickle.dumps(test_data))

    handler = AsyncPklHandler()
    result = await handler.fetch(tmp_path, "test.pkl")

    assert result == test_data


@pytest.mark.asyncio
async def test_async_pkl_store_basic(tmp_path):
    """Test basic async store to pickle file."""
    import pickle
    handler = AsyncPklHandler()
    test_data = [{"name": "Charlie", "age": 35}]
    rows_written = await handler.store(test_data, tmp_path, "output.pkl")

    assert rows_written == 1

    # Verify file content
    result_file = tmp_path / "output.pkl"
    result = pickle.loads(result_file.read_bytes())
    assert result == test_data
