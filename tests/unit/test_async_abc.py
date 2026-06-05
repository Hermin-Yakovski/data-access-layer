import pytest
from data_access_layer.abc import AsyncDataHandler

def test_async_data_handler_is_abstract():
    """AsyncDataHandler should be an abstract class."""
    with pytest.raises(TypeError):
        AsyncDataHandler()

def test_async_data_handler_requires_fetch():
    """Subclass must implement async fetch."""
    class IncompleteHandler(AsyncDataHandler):
        async def store(self, data, path, table, **kwargs):
            return 0

    with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteHandler"):
        IncompleteHandler()

def test_async_data_handler_requires_store():
    """Subclass must implement async store."""
    class IncompleteHandler(AsyncDataHandler):
        async def fetch(self, path, table, **kwargs):
            return []

    with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteHandler"):
        IncompleteHandler()
