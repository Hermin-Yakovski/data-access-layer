# Type Coercion and Post-Processing Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automatic type coercion to data layer and refactor duplicated post-processing logic into a unified mixin.

**Architecture:** Create `PostProcessingMixin` that centralizes column selection, filtering, limiting, and type coercion. All handlers inherit from this mixin, reducing code duplication and adding the new types parameter.

**Tech Stack:** Python 3.8+, typing module, pytest for testing

---

## File Structure

**New file:**
- `dal/post_processing.py` - PostProcessingMixin with _coerce_value, _coerce_row, _select_columns, _apply_processing

**New test file:**
- `tests/unit/test_post_processing.py` - Unit tests for PostProcessingMixin

**Modified files:**
- `dal/json_handler.py` - Inherit PostProcessingMixin, add types param, use _apply_processing
- `dal/csv_handler.py` - Inherit PostProcessingMixin, add types param, use _apply_processing
- `dal/pkl_handler.py` - Inherit PostProcessingMixin, add types param, use _apply_processing
- `dal/xlsx_handler.py` - Inherit PostProcessingMixin, add types param, use _apply_processing
- `dal/sqlite_handler.py` - Inherit PostProcessingMixin, add types param, use _apply_processing

**Modified test files:**
- `tests/unit/test_json_handler.py` - Add type coercion tests
- `tests/unit/test_csv_handler.py` - Add type coercion tests
- `tests/unit/test_pkl_handler.py` - Add type coercion tests
- `tests/unit/test_xlsx_handler.py` - Add type coercion tests
- `tests/unit/test_sqlite_handler.py` - Add type coercion tests

---

## Task 1: Create PostProcessingMixin with type coercion methods

**Files:**
- Create: `dal/post_processing.py`

- [ ] **Step 1: Write failing test for _coerce_value - int conversion**

Create test file: `tests/unit/test_post_processing.py`

```python
import pytest
from dal.post_processing import PostProcessingMixin


class TestCoerceValue:
    def test_coerce_string_to_int(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value("123", int)
        assert result == 123
        assert isinstance(result, int)

    def test_coerce_none_to_int(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(None, int)
        assert result == 0
        assert isinstance(result, int)

    def test_coerce_float_to_int(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(3.14, int)
        assert result == 3
        assert isinstance(result, int)

    def test_coerce_bool_to_int(self):
        mixin = PostProcessingMixin()
        assert mixin._coerce_value(True, int) == 1
        assert mixin._coerce_value(False, int) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_post_processing.py::TestCoerceValue::test_coerce_string_to_int -v`

Expected: FAIL with "PostProcessingMixin not found" or "_coerce_value not defined"

- [ ] **Step 3: Create PostProcessingMixin with _coerce_value for int**

Create: `dal/post_processing.py`

```python
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Type


class PostProcessingMixin:
    """Provides post-processing capabilities for data handlers.

    Centralizes logic for type coercion, column selection, filtering,
    and limiting that was previously duplicated across all handlers.
    """

    def _coerce_value(self, value: Any, target_type: Type) -> Any:
        """Coerce a single value to the target type.

        Handles None values by converting to defaults.
        Raises TypeError on conversion failure.

        Args:
            value: The value to coerce
            target_type: The type to coerce to (int, float, str, bool)

        Returns:
            The coerced value

        Raises:
            TypeError: If conversion fails
        """
        if value is None:
            if target_type == int:
                return 0
            elif target_type == float:
                return 0.0
            elif target_type == str:
                return ""
            elif target_type == bool:
                return False
            else:
                raise TypeError(f"Unsupported target type: {target_type}")

        try:
            if target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == str:
                return str(value)
            elif target_type == bool:
                if isinstance(value, str):
                    lower_val = value.lower()
                    if lower_val in ("true", "1", "yes"):
                        return True
                    elif lower_val in ("false", "0", "no"):
                        return False
                    else:
                        raise ValueError(f"Cannot convert '{value}' to bool")
                return bool(value)
            else:
                raise TypeError(f"Unsupported target type: {target_type}")
        except (ValueError, TypeError) as e:
            raise TypeError(f"Cannot convert {type(value).__name__} value '{value}' to {target_type.__name__}") from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_post_processing.py::TestCoerceValue -v`

Expected: PASS for all int coercion tests

- [ ] **Step 5: Commit**

```bash
git add dal/post_processing.py tests/unit/test_post_processing.py
git commit -m "feat: add PostProcessingMixin with _coerce_value for int type"
```

---

## Task 2: Add _coerce_value support for float, str, bool

**Files:**
- Modify: `dal/post_processing.py`
- Modify: `tests/unit/test_post_processing.py`

- [ ] **Step 1: Write failing tests for float, str, bool coercion**

Add to `tests/unit/test_post_processing.py`:

```python
class TestCoerceValueFloat:
    def test_coerce_string_to_float(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value("3.14", float)
        assert result == 3.14
        assert isinstance(result, float)

    def test_coerce_none_to_float(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(None, float)
        assert result == 0.0
        assert isinstance(result, float)

    def test_coerce_int_to_float(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(42, float)
        assert result == 42.0


class TestCoerceValueStr:
    def test_coerce_int_to_str(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(123, str)
        assert result == "123"

    def test_coerce_none_to_str(self):
        mixin = PostProcessingMixin()
        result = mixin._coerce_value(None, str)
        assert result == ""

    def test_coerce_bool_to_str(self):
        mixin = PostProcessingMixin()
        assert mixin._coerce_value(True, str) == "True"
        assert mixin._coerce_value(False, str) == "False"


class TestCoerceValueBool:
    def test_coerce_string_true_to_bool(self):
        mixin = PostProcessingMixin()
        for val in ["true", "True", "TRUE", "1", "yes"]:
            assert mixin._coerce_value(val, bool) is True

    def test_coerce_string_false_to_bool(self):
        mixin = PostProcessingMixin()
        for val in ["false", "False", "FALSE", "0", "no"]:
            assert mixin._coerce_value(val, bool) is False

    def test_coerce_none_to_bool(self):
        mixin = PostProcessingMixin()
        assert mixin._coerce_value(None, bool) is False

    def test_coerce_int_to_bool(self):
        mixin = PostProcessingMixin()
        assert mixin._coerce_value(0, bool) is False
        assert mixin._coerce_value(1, bool) is True
        assert mixin._coerce_value(42, bool) is True


class TestCoerceValueErrors:
    def test_invalid_string_to_int_raises_typeerror(self):
        mixin = PostProcessingMixin()
        with pytest.raises(TypeError, match="Cannot convert str value 'abc' to int"):
            mixin._coerce_value("abc", int)

    def test_invalid_string_to_float_raises_typeerror(self):
        mixin = PostProcessingMixin()
        with pytest.raises(TypeError, match="Cannot convert str value 'xyz' to float"):
            mixin._coerce_value("xyz", float)

    def test_unsupported_type_raises_typeerror(self):
        mixin = PostProcessingMixin()
        with pytest.raises(TypeError, match="Unsupported target type"):
            mixin._coerce_value(123, list)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_post_processing.py -v`

Expected: All tests should pass (float, str, bool already implemented in Task 1)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_post_processing.py
git commit -m "test: add comprehensive tests for float, str, bool coercion"
```

---

## Task 3: Implement _coerce_row method

**Files:**
- Modify: `dal/post_processing.py`
- Modify: `tests/unit/test_post_processing.py`

- [ ] **Step 1: Write failing tests for _coerce_row**

Add to `tests/unit/test_post_processing.py`:

```python
class TestCoerceRow:
    def test_coerce_fields_in_both_row_and_types(self):
        mixin = PostProcessingMixin()
        row = {'id': '123', 'name': 'Alice', 'age': '30'}
        types = {'id': int, 'age': int}
        result = mixin._coerce_row(row, types)
        assert result == {'id': 123, 'name': 'Alice', 'age': 30}
        assert isinstance(result['id'], int)
        assert isinstance(result['age'], int)

    def test_keep_fields_not_in_types(self):
        mixin = PostProcessingMixin()
        row = {'id': '123', 'name': 'Alice'}
        types = {'id': int}
        result = mixin._coerce_row(row, types)
        assert result == {'id': 123, 'name': 'Alice'}
        assert result['name'] == 'Alice'  # unchanged

    def test_skip_fields_in_types_not_in_row(self):
        mixin = PostProcessingMixin()
        row = {'id': '123'}
        types = {'id': int, 'name': str}
        result = mixin._coerce_row(row, types)
        assert result == {'id': 123}
        assert 'name' not in result

    def test_empty_types_dict_returns_unchanged(self):
        mixin = PostProcessingMixin()
        row = {'id': '123', 'name': 'Alice'}
        types = {}
        result = mixin._coerce_row(row, types)
        assert result == row

    def test_empty_row_returns_empty_dict(self):
        mixin = PostProcessingMixin()
        row = {}
        types = {'id': int}
        result = mixin._coerce_row(row, types)
        assert result == {}

    def test_coercion_failure_raises_typeerror(self):
        mixin = PostProcessingMixin()
        row = {'age': 'not_a_number'}
        types = {'age': int}
        with pytest.raises(TypeError, match="Failed to coerce field 'age'"):
            mixin._coerce_row(row, types)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_post_processing.py::TestCoerceRow -v`

Expected: FAIL with "_coerce_row not defined"

- [ ] **Step 3: Implement _coerce_row method**

Add to `dal/post_processing.py`:

```python
    def _coerce_row(self, row: Dict[str, Any], types: Dict[str, Type]) -> Dict[str, Any]:
        """Coerce values in a row to their target types.

        Behavior:
        - Field in row AND types: coerce to target type
        - Field in row NOT in types: keep original value
        - Field in types NOT in row: skip silently

        Args:
            row: The row dictionary to process
            types: Dictionary mapping field names to target types

        Returns:
            A new row dictionary with coerced values

        Raises:
            TypeError: If coercion fails for a field
        """
        result = {}
        for field_name, value in row.items():
            if field_name in types:
                try:
                    result[field_name] = self._coerce_value(value, types[field_name])
                except TypeError as e:
                    raise TypeError(f"Failed to coerce field '{field_name}': {e}") from e
            else:
                result[field_name] = value
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_post_processing.py::TestCoerceRow -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/post_processing.py tests/unit/test_post_processing.py
git commit -m "feat: add _coerce_row method to PostProcessingMixin"
```

---

## Task 4: Implement _select_columns method

**Files:**
- Modify: `dal/post_processing.py`
- Modify: `tests/unit/test_post_processing.py`

- [ ] **Step 1: Write failing test for _select_columns**

Add to `tests/unit/test_post_processing.py`:

```python
class TestSelectColumns:
    def test_select_columns_from_row(self):
        mixin = PostProcessingMixin()
        row = {'id': 1, 'name': 'Alice', 'age': 30, 'city': 'NYC'}
        cols = {'id', 'name'}
        result = mixin._select_columns(row, cols)
        assert result == {'id': 1, 'name': 'Alice'}

    def test_select_columns_empty_set(self):
        mixin = PostProcessingMixin()
        row = {'id': 1, 'name': 'Alice'}
        cols = set()
        result = mixin._select_columns(row, cols)
        assert result == {}

    def test_select_columns_all_present(self):
        mixin = PostProcessingMixin()
        row = {'id': 1, 'name': 'Alice'}
        cols = {'id', 'name'}
        result = mixin._select_columns(row, cols)
        assert result == row

    def test_select_columns_some_missing(self):
        mixin = PostProcessingMixin()
        row = {'id': 1, 'name': 'Alice'}
        cols = {'id', 'name', 'age'}
        result = mixin._select_columns(row, cols)
        assert result == {'id': 1, 'name': 'Alice'}
        assert 'age' not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_post_processing.py::TestSelectColumns -v`

Expected: FAIL with "_select_columns not defined"

- [ ] **Step 3: Implement _select_columns method**

Add to `dal/post_processing.py`:

```python
    def _select_columns(self, row: Dict[str, Any], cols: Set[str]) -> Dict[str, Any]:
        """Select specified columns from a row.

        Args:
            row: The row dictionary
            cols: Set of column names to select

        Returns:
            A new dictionary with only the specified columns
        """
        return {k: v for k, v in row.items() if k in cols}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_post_processing.py::TestSelectColumns -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/post_processing.py tests/unit/test_post_processing.py
git commit -m "feat: add _select_columns method to PostProcessingMixin"
```

---

## Task 5: Implement _apply_processing unified method

**Files:**
- Modify: `dal/post_processing.py`
- Modify: `tests/unit/test_post_processing.py`

- [ ] **Step 1: Write failing tests for _apply_processing**

Add to `tests/unit/test_post_processing.py`:

```python
class TestApplyProcessing:
    def test_apply_processing_only_types(self):
        mixin = PostProcessingMixin()
        data = [{'id': '1', 'name': 'Alice'}, {'id': '2', 'name': 'Bob'}]
        result = mixin._apply_processing(data, types={'id': int})
        assert result == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        assert all(isinstance(r['id'], int) for r in result)

    def test_apply_processing_only_cols(self):
        mixin = PostProcessingMixin()
        data = [{'id': 1, 'name': 'Alice', 'age': 30}, {'id': 2, 'name': 'Bob', 'age': 25}]
        result = mixin._apply_processing(data, cols=['id', 'name'])
        assert result == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

    def test_apply_processing_only_filter(self):
        mixin = PostProcessingMixin()
        data = [{'id': 1, 'active': True}, {'id': 2, 'active': False}, {'id': 3, 'active': True}]
        result = mixin._apply_processing(data, filter_=lambda r: r['active'])
        assert result == [{'id': 1, 'active': True}, {'id': 3, 'active': True}]

    def test_apply_processing_only_limit(self):
        mixin = PostProcessingMixin()
        data = [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}, {'id': 5}]
        result = mixin._apply_processing(data, limit=3)
        assert len(result) == 3
        assert result == [{'id': 1}, {'id': 2}, {'id': 3}]

    def test_apply_processing_order(self):
        """Verify processing order: types -> cols -> filter -> limit"""
        mixin = PostProcessingMixin()
        data = [
            {'id': '1', 'name': 'Alice', 'age': '30', 'active': 'true'},
            {'id': '2', 'name': 'Bob', 'age': '25', 'active': 'false'},
            {'id': '3', 'name': 'Charlie', 'age': '35', 'active': 'true'},
        ]
        result = mixin._apply_processing(
            data,
            types={'id': int, 'age': int, 'active': bool},
            cols=['id', 'age', 'active'],
            filter_=lambda r: r['active'],  # filter after coercion and column selection
            limit=1
        )
        # First row: types coerced, cols selected, active=True so passes filter
        assert result == [{'id': 1, 'age': 30, 'active': True}]
        assert isinstance(result[0]['id'], int)
        assert isinstance(result[0]['age'], int)
        assert isinstance(result[0]['active'], bool)

    def test_apply_processing_none_params_returns_unchanged(self):
        mixin = PostProcessingMixin()
        data = [{'id': 1, 'name': 'Alice'}]
        result = mixin._apply_processing(data)
        assert result == data

    def test_apply_processing_empty_data(self):
        mixin = PostProcessingMixin()
        data = []
        result = mixin._apply_processing(data, types={'id': int}, cols=['id'])
        assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_post_processing.py::TestApplyProcessing -v`

Expected: FAIL with "_apply_processing not defined"

- [ ] **Step 3: Implement _apply_processing method**

Add to `dal/post_processing.py`:

```python
    def _apply_processing(
        self,
        data: List[Dict[str, Any]],
        types: Optional[Dict[str, Type]] = None,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Apply all post-processing steps in order.

        Processing order:
        1. Type coercion
        2. Column selection
        3. Filtering
        4. Limiting

        Args:
            data: List of row dictionaries
            types: Optional dict mapping field names to target types
            cols: Optional iterable of column names to select
            filter_: Optional callable for row filtering
            limit: Optional maximum number of rows to return

        Returns:
            Processed list of row dictionaries
        """
        result = data

        # Step 1: Type coercion
        if types is not None:
            result = [self._coerce_row(row, types) for row in result]

        # Step 2: Column selection
        if cols is not None:
            cols_set = set(cols)
            result = [self._select_columns(row, cols_set) for row in result]

        # Step 3: Filtering
        if filter_ is not None:
            result = [row for row in result if filter_(row)]

        # Step 4: Limiting
        if limit is not None:
            result = result[:limit]

        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_post_processing.py::TestApplyProcessing -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dal/post_processing.py tests/unit/test_post_processing.py
git commit -m "feat: add _apply_processing unified method to PostProcessingMixin"
```

---

## Task 6: Refactor JsonHandler to use PostProcessingMixin

**Files:**
- Modify: `dal/json_handler.py`

- [ ] **Step 1: Update JsonHandler to inherit PostProcessingMixin**

Modify `dal/json_handler.py`:

```python
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import DataHandler
from .post_processing import PostProcessingMixin  # NEW


class JsonHandler(PostProcessingMixin, DataHandler):  # MODIFIED
    """Handler for JSON format files.

    Supports fetching and storing data in JSON format with optional
    encoding and indentation configuration.
    """
```

- [ ] **Step 2: Update JsonHandler.fetch() signature and implementation**

Replace the fetch method in `dal/json_handler.py`:

```python
    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> List[Dict[str, Any]]:
        """Fetch data from JSON file.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            with open(file_path, "r", encoding=self.encoding) as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(
                    f"JSON file must contain a list of objects, got {type(data).__name__}"
                )

            # Validate that all items are dictionaries
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSON file must contain a list of dictionaries, but item at index {i} is {type(row).__name__}"
                    )

            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)

            return data

        except Exception:
            if strict:
                raise
            return []
```

- [ ] **Step 3: Update JsonHandler.store() signature and implementation**

Replace the store method in `dal/json_handler.py`:

```python
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
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> int:
        """Store data to JSON file.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table

            # Prepare data to store
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                with open(file_path, "r", encoding=self.encoding) as f:
                    existing_data = json.load(f)
                if isinstance(existing_data, list):
                    data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, "w", encoding=self.encoding) as f:
                json.dump(data_to_store, f, indent=self.indent, ensure_ascii=False)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run existing tests to ensure no regression**

Run: `pytest tests/unit/test_json_handler.py -v`

Expected: All existing tests PASS (behavior unchanged when types=None)

- [ ] **Step 5: Commit**

```bash
git add dal/json_handler.py
git commit -m "refactor: JsonHandler now uses PostProcessingMixin"
```

---

## Task 7: Add type coercion tests for JsonHandler

**Files:**
- Modify: `tests/unit/test_json_handler.py`

- [ ] **Step 1: Write integration tests for JsonHandler type coercion**

Add to `tests/unit/test_json_handler.py`:

```python
class TestJsonHandlerTypeCoercion:
    def test_fetch_with_types_coerces_strings_to_int(self):
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30'}],
            path=test_path,
            table='test_types.json'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types.json',
            types={'id': int, 'age': int}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)
        assert result[0]['name'] == 'Alice'  # unchanged

    def test_fetch_with_types_and_cols(self):
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30', 'active': 'true'}],
            path=test_path,
            table='test_types_cols.json'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types_cols.json',
            types={'id': int, 'age': int, 'active': bool},
            cols=['id', 'age', 'active']
        )

        assert result == [{'id': 1, 'age': 30, 'active': True}]
        assert isinstance(result[0]['active'], bool)

    def test_fetch_with_types_and_filter(self):
        handler = JsonHandler()
        handler.store(
            [
                {'id': '1', 'age': '30'},
                {'id': '2', 'age': '25'},
                {'id': '3', 'age': '35'}
            ],
            path=test_path,
            table='test_types_filter.json'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types_filter.json',
            types={'age': int},
            filter_=lambda r: r['age'] > 28
        )

        assert len(result) == 2
        assert result[0]['id'] == '1'
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)

    def test_fetch_with_types_coercion_failure_raises_typeerror(self):
        handler = JsonHandler()
        handler.store(
            [{'id': '1', 'age': 'not_a_number'}],
            path=test_path,
            table='test_types_error.json'
        )

        with pytest.raises(TypeError, match="Failed to coerce field 'age'"):
            handler.fetch(
                path=test_path,
                table='test_types_error.json',
                types={'age': int}
            )

    def test_store_with_types_coerces_before_writing(self):
        handler = JsonHandler()
        handler.store(
            [{'id': 1, 'name': 'Alice', 'age': 30}],  # ints
            path=test_path,
            table='test_store_types.json',
            types={'id': str, 'name': str, 'age': str}  # coerce to strings
        )

        # Read back without coercion to verify stored as strings
        result = handler.fetch(path=test_path, table='test_store_types.json')

        assert result[0]['id'] == '1'
        assert isinstance(result[0]['id'], str)
        assert result[0]['age'] == '30'
        assert isinstance(result[0]['age'], str)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_json_handler.py::TestJsonHandlerTypeCoercion -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_json_handler.py
git commit -m "test: add type coercion tests for JsonHandler"
```

---

## Task 8: Refactor CsvHandler to use PostProcessingMixin

**Files:**
- Modify: `dal/csv_handler.py`

- [ ] **Step 1: Update CsvHandler imports and class declaration**

Modify `dal/csv_handler.py`:

```python
import csv
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import DataHandler
from .post_processing import PostProcessingMixin  # NEW


class CsvHandler(PostProcessingMixin, DataHandler):  # MODIFIED
    """Handler for CSV format files.

    Supports fetching and storing data in CSV format with optional
    delimiter and encoding configuration.
    """
```

- [ ] **Step 2: Update CsvHandler.fetch() method**

Replace fetch method with:

```python
    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> List[Dict[str, Any]]:
        """Fetch data from CSV file.

        Args:
            path: Directory containing the file
            table: Filename to fetch from
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to return (applied after filtering)
            strict: If True, raise exceptions; if False, return empty list on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            List of row dictionaries
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            with open(file_path, "r", encoding=self.encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                data = list(reader)

            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)

            return data

        except Exception:
            if strict:
                raise
            return []
```

- [ ] **Step 3: Update CsvHandler.store() method**

Replace store method with:

```python
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
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> int:
        """Store data to CSV file.

        Args:
            data: List of row dictionaries to store
            path: Directory containing the file
            table: Filename to store to
            cols: Columns to include (allowlist, None = all columns)
            filter_: Optional callable for row filtering
            limit: Maximum rows to store (applied after filtering)
            overwrite: If True, replace existing file; if False, append
            strict: If True, raise exceptions; if False, return 0 on error
            types: Optional dict mapping field names to target types for coercion

        Returns:
            Number of rows stored
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory '{path}' does not exist")

            file_path = path / table

            # Prepare data to store
            data_to_store = data.copy()

            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)

            # Determine fieldnames from data
            if data_to_store:
                fieldnames = list(data_to_store[0].keys())
            else:
                fieldnames = []

            # For append mode, read existing data and merge
            if not overwrite and file_path.exists():
                existing_data = []
                with open(file_path, "r", encoding=self.encoding, newline="") as f:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    existing_data = list(reader)
                data_to_store = existing_data + data_to_store

            # Write to file
            with open(file_path, "w", encoding=self.encoding, newline="") as f:
                if data_to_store:
                    fieldnames = list(data_to_store[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
                    writer.writeheader()
                    writer.writerows(data_to_store)

            return len(data_to_store)

        except Exception:
            if strict:
                raise
            return 0
```

- [ ] **Step 4: Run existing tests to ensure no regression**

Run: `pytest tests/unit/test_csv_handler.py -v`

Expected: All existing tests PASS

- [ ] **Step 5: Commit**

```bash
git add dal/csv_handler.py
git commit -m "refactor: CsvHandler now uses PostProcessingMixin"
```

---

## Task 9: Add type coercion tests for CsvHandler

**Files:**
- Modify: `tests/unit/test_csv_handler.py`

- [ ] **Step 1: Add type coercion tests to CsvHandler test file**

Add similar tests to `tests/unit/test_csv_handler.py`:

```python
class TestCsvHandlerTypeCoercion:
    def test_fetch_with_types_coerces_csv_strings(self):
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30'}],
            path=test_path,
            table='test_types.csv'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types.csv',
            types={'id': int, 'age': int}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['age'] == 30
        assert isinstance(result[0]['age'], int)

    def test_fetch_with_types_and_filter(self):
        handler = CsvHandler()
        handler.store(
            [{'id': '1', 'age': '30'}, {'id': '2', 'age': '25'}, {'id': '3', 'age': '35'}],
            path=test_path,
            table='test_types_filter.csv'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types_filter.csv',
            types={'age': int},
            filter_=lambda r: r['age'] > 28
        )

        assert len(result) == 2
        assert result[0]['age'] == 30
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_csv_handler.py::TestCsvHandlerTypeCoercion -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_csv_handler.py
git commit -m "test: add type coercion tests for CsvHandler"
```

---

## Task 10: Refactor PklHandler to use PostProcessingMixin

**Files:**
- Modify: `dal/pkl_handler.py`

- [ ] **Step 1: Update PklHandler imports and class declaration**

Modify `dal/pkl_handler.py`:

```python
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import DataHandler
from .post_processing import PostProcessingMixin  # NEW


class PklHandler(PostProcessingMixin, DataHandler):  # MODIFIED
    """Handler for Python pickle format files."""
```

- [ ] **Step 2: Update PklHandler.fetch() signature**

Add types parameter to fetch method signature:

```python
    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> List[Dict[str, Any]]:
```

- [ ] **Step 3: Replace post-processing in fetch with _apply_processing call**

Replace lines 60-72 in `dal/pkl_handler.py` with:

```python
            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)
```

- [ ] **Step 4: Update PklHandler.store() signature**

Add types parameter to store method signature:

```python
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
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> int:
```

- [ ] **Step 5: Replace post-processing in store with _apply_processing call**

Replace lines 120-132 in `dal/pkl_handler.py` with:

```python
            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)
```

- [ ] **Step 6: Run existing tests to ensure no regression**

Run: `pytest tests/unit/test_pkl_handler.py -v`

Expected: All existing tests PASS

- [ ] **Step 7: Commit**

```bash
git add dal/pkl_handler.py
git commit -m "refactor: PklHandler now uses PostProcessingMixin"
```

---

## Task 11: Add type coercion tests for PklHandler

**Files:**
- Modify: `tests/unit/test_pkl_handler.py`

- [ ] **Step 1: Add type coercion tests to PklHandler test file**

Add to `tests/unit/test_pkl_handler.py`:

```python
class TestPklHandlerTypeCoercion:
    def test_fetch_with_types_coerces_values(self):
        handler = PklHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'active': 'true'}],
            path=test_path,
            table='test_types.pkl'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types.pkl',
            types={'id': int, 'active': bool}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['active'] is True
        assert isinstance(result[0]['active'], bool)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_pkl_handler.py::TestPklHandlerTypeCoercion -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_pkl_handler.py
git commit -m "test: add type coercion tests for PklHandler"
```

---

## Task 12: Refactor XlsxHandler to use PostProcessingMixin

**Files:**
- Modify: `dal/xlsx_handler.py`

- [ ] **Step 1: Update XlsxHandler imports and class declaration**

Modify `dal/xlsx_handler.py`:

```python
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

try:
    from openpyxl import load_workbook, Workbook
    from openpyxl.worksheet.worksheet import Worksheet
except ImportError:
    load_workbook = Workbook = Worksheet = None  # type: ignore

from .abc import DataHandler
from .post_processing import PostProcessingMixin  # NEW


class XlsxHandler(PostProcessingMixin, DataHandler):  # MODIFIED
    """Handler for Excel XLSX format files (requires openpyxl)."""
```

- [ ] **Step 2: Update XlsxHandler.fetch() method**

Update fetch signature and replace post-processing:

```python
    def fetch(
        self,
        path: Path,
        table: str,
        cols: Optional[Iterable[str]] = None,
        filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
        strict: bool = True,
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> List[Dict[str, Any]]:
```

Replace post-processing lines (around lines 56-68) with:

```python
            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)
```

- [ ] **Step 3: Update XlsxHandler.store() method**

Update store signature:

```python
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
        types: Optional[Dict[str, Type]] = None,  # NEW
    ) -> int:
```

Replace post-processing lines (around lines 106-118) with:

```python
            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)
```

- [ ] **Step 4: Run existing tests to ensure no regression**

Run: `pytest tests/unit/test_xlsx_handler.py -v`

Expected: All existing tests PASS

- [ ] **Step 5: Commit**

```bash
git add dal/xlsx_handler.py
git commit -m "refactor: XlsxHandler now uses PostProcessingMixin"
```

---

## Task 13: Add type coercion tests for XlsxHandler

**Files:**
- Modify: `tests/unit/test_xlsx_handler.py`

- [ ] **Step 1: Add type coercion tests to XlsxHandler test file**

Add to `tests/unit/test_xlsx_handler.py`:

```python
class TestXlsxHandlerTypeCoercion:
    def test_fetch_with_types_coerces_values(self):
        handler = XlsxHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'age': '30'}],
            path=test_path,
            table='test_types.xlsx'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types.xlsx',
            types={'id': int, 'age': int}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['age'] == 30
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_xlsx_handler.py::TestXlsxHandlerTypeCoercion -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_xlsx_handler.py
git commit -m "test: add type coercion tests for XlsxHandler"
```

---

## Task 14: Refactor SqliteHandler to use PostProcessingMixin

**Files:**
- Modify: `dal/sqlite_handler.py`

- [ ] **Step 1: Read SqliteHandler to understand current implementation**

Run: `cat dal/sqlite_handler.py`

- [ ] **Step 2: Update SqliteHandler imports and class declaration**

Modify `dal/sqlite_handler.py`:

```python
import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from .abc import DataHandler
from .post_processing import PostProcessingMixin  # NEW


class SqliteHandler(PostProcessingMixin, DataHandler):  # MODIFIED
    """Handler for SQLite database files."""
```

- [ ] **Step 3: Update SqliteHandler.fetch() signature and add types parameter**

Update fetch method signature to add types parameter.

- [ ] **Step 4: Replace post-processing in fetch with _apply_processing call**

Locate the post-processing section (cols, filter_, limit) and replace with:

```python
            # Use unified post-processing
            data = self._apply_processing(data, types, cols, filter_, limit)
```

- [ ] **Step 5: Update SqliteHandler.store() signature and add types parameter**

Update store method signature to add types parameter.

- [ ] **Step 6: Replace post-processing in store with _apply_processing call**

Locate the post-processing section and replace with:

```python
            # Use unified post-processing
            data_to_store = self._apply_processing(data_to_store, types, cols, filter_, limit)
```

- [ ] **Step 7: Run existing tests to ensure no regression**

Run: `pytest tests/unit/test_sqlite_handler.py -v`

Expected: All existing tests PASS

- [ ] **Step 8: Commit**

```bash
git add dal/sqlite_handler.py
git commit -m "refactor: SqliteHandler now uses PostProcessingMixin"
```

---

## Task 15: Add type coercion tests for SqliteHandler

**Files:**
- Modify: `tests/unit/test_sqlite_handler.py`

- [ ] **Step 1: Add type coercion tests to SqliteHandler test file**

Add to `tests/unit/test_sqlite_handler.py`:

```python
class TestSqliteHandlerTypeCoercion:
    def test_fetch_with_types_coerces_values(self):
        handler = SqliteHandler()
        handler.store(
            [{'id': '1', 'name': 'Alice', 'active': 'true'}],
            path=test_path,
            table='test_types.db'
        )

        result = handler.fetch(
            path=test_path,
            table='test_types',
            types={'id': int, 'active': bool}
        )

        assert result[0]['id'] == 1
        assert isinstance(result[0]['id'], int)
        assert result[0]['active'] is True
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_sqlite_handler.py::TestSqliteHandlerTypeCoercion -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_sqlite_handler.py
git commit -m "test: add type coercion tests for SqliteHandler"
```

---

## Task 16: Run full test suite and verify backward compatibility

**Files:**
- None (verification task)

- [ ] **Step 1: Run all unit tests**

Run: `pytest tests/unit/ -v`

Expected: All tests PASS

- [ ] **Step 2: Run all integration tests**

Run: `pytest tests/integration/ -v`

Expected: All tests PASS

- [ ] **Step 3: Verify no breaking changes with test script**

Create a quick verification script:

```python
from pathlib import Path
from dal import JsonHandler

# This should work exactly as before (no types param)
handler = JsonHandler()
data = [{'id': 1, 'name': 'Alice'}]
handler.store(data, path=Path('test_output'), table='test.json')
result = handler.fetch(path=Path('test_output'), table='test.json')
assert result == data
print("Backward compatibility verified!")
```

Run: `python test_backward_compat.py`

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "test: verify full test suite passes and backward compatibility maintained"
```

---

## Task 17: Update documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with types parameter documentation**

Add to the API Reference section in `README.md`:

```markdown
### Type Coercion

All handlers support automatic type coercion via the `types` parameter:

```python
from dal import JsonHandler

handler = JsonHandler()

# Fetch with type coercion
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'id': int, 'age': int, 'active': bool}
)

# Type guarantees:
for row in data:
    user_id: int = row['id']      # Guaranteed to be int
    age: int = row['age']          # Guaranteed to be int
    active: bool = row['active']   # Guaranteed to be bool

# Store with type coercion
handler.store(
    data=new_users,
    path=Path("output"),
    table="users.json",
    types={'id': str, 'age': str}  # Convert to strings before storing
)
```

**Supported types:** `int`, `float`, `str`, `bool`

**Type coercion rules:**
- `None` values convert to defaults (0, 0.0, "", False)
- String conversions follow Python's built-in conversion rules
- Bool strings are case-insensitive ("true", "false", "1", "0")
```

- [ ] **Step 2: Update processing order documentation**

Update the "Data Processing Order" section to include type coercion:

```markdown
## Data Processing Order

Operations are applied in the following order:

1. **Type coercion** (`types`): Convert values to specified types
2. **Column selection** (`cols`): Select specific columns
3. **Filtering** (`filter_`): Apply filter function to rows
4. **Limiting** (`limit`): Apply limit to filtered results
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with type coercion documentation"
```

---

## Self-Review Checklist

**Spec Coverage:**
- [x] Type coercion feature (Tasks 1-3, 7, 9, 11, 13, 15)
- [x] PostProcessingMixin with all methods (Tasks 1-5)
- [x] All handlers refactored (Tasks 6, 8, 10, 12, 14)
- [x] Comprehensive tests (Tasks 2-5, 7, 9, 11, 13, 15, 16)
- [x] Documentation updated (Task 17)
- [x] Backward compatibility verified (Task 16)

**Placeholder Scan:**
- [x] No TBD or TODO found
- [x] All code blocks contain actual code
- [x] All commands are exact and runnable
- [x] All file paths are specified

**Type Consistency:**
- [x] Method names consistent (_coerce_value, _coerce_row, _select_columns, _apply_processing)
- [x] Parameter names consistent (types, cols, filter_, limit)
- [x] Type imports consistent across all handlers
