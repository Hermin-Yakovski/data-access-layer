from .abc import DataHandler
from .json_handler import JsonHandler
from .csv_handler import CsvHandler
from .pkl_handler import PklHandler

try:
    from .xlsx_handler import XlsxHandler
    _xlsx_available = True
except ImportError:
    _xlsx_available = False

if _xlsx_available:
    __all__ = ["DataHandler", "JsonHandler", "CsvHandler", "PklHandler", "XlsxHandler"]
else:
    __all__ = ["DataHandler", "JsonHandler", "CsvHandler", "PklHandler"]
