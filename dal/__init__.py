from .abc import AsyncDataHandler, DataHandler
from .json_handler import AsyncJsonHandler, JsonHandler
from .csv_handler import CsvHandler
from .pkl_handler import PklHandler
from .sqlite_handler import SqliteHandler

try:
    from .xlsx_handler import XlsxHandler

    _xlsx_available = True
except ImportError:
    _xlsx_available = False

if _xlsx_available:
    __all__ = ["DataHandler", "AsyncDataHandler", "JsonHandler", "AsyncJsonHandler", "CsvHandler", "PklHandler", "SqliteHandler", "XlsxHandler"]
else:
    __all__ = ["DataHandler", "AsyncDataHandler", "JsonHandler", "AsyncJsonHandler", "CsvHandler", "PklHandler", "SqliteHandler"]
