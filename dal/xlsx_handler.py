from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

try:
    from openpyxl import Workbook, load_workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from .abc import DataHandler


class XlsxHandler(DataHandler):
    """Handler for Excel XLSX format files.

    Supports fetching and storing data in XLSX format with optional
    sheet_name and header_row configuration.

    Requires openpyxl to be installed. If not available, imports will fail.
    """

    def __init__(self, sheet_name: str = 'Sheet1', header_row: int = 0):
        """Initialize XlsxHandler.

        Args:
            sheet_name: Name of the sheet to read/write (default: 'Sheet1')
            header_row: Row number containing column headers (0-indexed, default: 0)

        Raises:
            ImportError: If openpyxl is not installed
        """
        if not HAS_OPENPYXL:
            raise ImportError("openpyxl is required for XlsxHandler. Install it with: pip install openpyxl")
        self.sheet_name = sheet_name
        self.header_row = header_row

    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch data from XLSX file.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            with load_workbook(file_path, read_only=True, data_only=True) as wb:
                ws = wb[self.sheet_name]

                # Get header row
                headers = None
                rows_data = []
                for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
                    if row_idx == self.header_row:
                        headers = [str(cell) if cell is not None else f"col_{i}" for i, cell in enumerate(row)]
                    elif row_idx > self.header_row:
                        rows_data.append(row)

                if headers is None:
                    raise ValueError(f"Header row {self.header_row} not found in sheet")

                # Convert rows to dictionaries
                data = []
                for row in rows_data:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                    data.append(row_dict)

            # Apply column selection
            if cols is not None:
                cols_set = set(cols)
                data = [{k: v for k, v in row.items() if k in cols_set} for row in data]

            # Apply filtering
            if filter_ is not None:
                data = [row for row in data if filter_(row)]

            # Apply limit (after filtering)
            if limit is not None:
                data = data[:limit]

            return data

        except Exception as e:
            if strict:
                raise
            return []

    def store(
        self,
        data: List[Dict[str, Any]],
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        overwrite: bool = True,
        strict: bool = True,
    ) -> int:
        """Store data to XLSX file.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table

            # Prepare data to store
            data_to_store = data.copy()

            # Apply column selection
            if cols is not None:
                cols_set = set(cols)
                data_to_store = [{k: v for k, v in row.items() if k in cols_set} for row in data_to_store]

            # Apply filtering
            if filter_ is not None:
                data_to_store = [row for row in data_to_store if filter_(row)]

            # Apply limit (after filtering)
            if limit is not None:
                data_to_store = data_to_store[:limit]

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                existing_data = self.fetch(
                    path=path,
                    table=table,
                    strict=True
                )
                data_to_store = existing_data + data_to_store

            # Create workbook and write data
            wb = Workbook()
            ws = wb.active
            ws.title = self.sheet_name

            if data_to_store:
                # Write header
                headers = list(data_to_store[0].keys())
                ws.append(headers)

                # Write data rows
                for row in data_to_store:
                    ws.append([row.get(h, "") for h in headers])

            # Save workbook
            wb.save(file_path)

            return len(data_to_store)

        except Exception as e:
            if strict:
                raise
            return 0
