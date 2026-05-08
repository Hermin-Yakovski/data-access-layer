# Type Coercion and Post-Processing Refactoring Design

**Date:** 2026-05-08
**Author:** Brainstorming Session
**Status:** Approved

## Overview

This design has two components:

1. **Add automatic type coercion** to the data access layer, allowing users to specify expected types for columns that will be applied during `fetch()` and `store()` operations. This eliminates the need for manual type casting and provides type guarantees at runtime.

2. **Refactor post-processing logic** by creating a `PostProcessingMixin` that consolidates duplicated code for column selection, filtering, limiting, and type coercion across all handlers. This reduces code duplication and ensures consistent behavior.

## Problem Statement

Currently, when fetching data, users must explicitly cast values to ensure type safety:

```python
for row in handler.fetch(...):
    index: int = row['id']  # No guarantee row['id'] is actually an int
    # Explicit casting required: index = int(row['id'])
```

This is error-prone and inelegant. Type coercion should be handled transparently by the data layer.

## Requirements

### Type Coercion (New Feature)
1. Add type coercion to both `fetch()` and `store()` methods
2. Define expected types via a per-call `types` parameter (e.g., `{'id': int, 'name': str}`)
3. Support basic types: `int`, `float`, `str`, `bool`
4. Handle `None` source values by converting to defaults (0, 0.0, "", False)
5. Raise `TypeError` on coercion failure when `strict=True`
6. Maintain backward compatibility (optional parameter, default behavior unchanged)

### Post-Processing Refactoring (Code Quality)
1. Create `PostProcessingMixin` to consolidate duplicated post-processing logic
2. Move column selection, filtering, and limiting logic from individual handlers into the mixin
3. Ensure consistent behavior across all handlers
4. Reduce code duplication (~100-150 lines across 5 handlers)

## Architecture

### PostProcessingMixin

A new mixin class providing centralized post-processing logic for all handlers. This consolidates the duplicated logic for column selection, filtering, limiting, and type coercion:

```python
class PostProcessingMixin:
    """Provides post-processing capabilities for data handlers.

    Centralizes logic for type coercion, column selection, filtering,
    and limiting that was previously duplicated across all handlers.
    """

    def _coerce_row(self, row: Dict[str, Any], types: Dict[str, Type]) -> Dict[str, Any]:
        """Coerce values in a row to their target types.

        Behavior:
        - Field in row AND types: coerce to target type
        - Field in row NOT in types: keep original value
        - Field in types NOT in row: skip silently
        """

    def _coerce_value(self, value: Any, target_type: Type) -> Any:
        """Coerce a single value to the target type.

        Handles None values by converting to defaults.
        Raises TypeError on conversion failure.
        """

    def _select_columns(self, row: Dict[str, Any], cols: Set[str]) -> Dict[str, Any]:
        """Select specified columns from a row."""

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
        """
```

### Handler Integration

All handlers inherit from both `PostProcessingMixin` and `DataHandler`:

```python
class JsonHandler(PostProcessingMixin, DataHandler):
    def fetch(self, ..., types: Optional[Dict[str, Type]] = None):
        # Load data
        data = self._load_from_file()

        # Apply all post-processing in one call
        data = self._apply_processing(data, types, cols, filter_, limit)

        return data
```

This eliminates code duplication across all handlers for:
- Column selection (currently duplicated)
- Filtering (currently duplicated)
- Limiting (currently duplicated)
- Type coercion (new feature)

## Coercion Rules

### int
- `None` → `0`
- String: `int("123")` → `123`
- Float: `int(3.14)` → `3`
- Bool: `int(True)` → `1`, `int(False)` → `0`

### float
- `None` → `0.0`
- String: `float("3.14")` → `3.14`
- Int: `float(42)` → `42.0`
- Bool: `float(True)` → `1.0`, `float(False)` → `0.0`

### str
- `None` → `""` (empty string)
- Any: `str(value)` (standard Python string conversion)

### bool
- `None` → `False`
- String: `"true"/"false"` (case-insensitive) → `True/False`
- Int: `0` → `False`, non-zero → `True`
- Float: `0.0` → `False`, non-zero → `True`

### Error Handling
- On conversion failure: raise `TypeError` with message: `"Failed to coerce field '<name>': cannot convert '<value>' to <type>"`

## API Changes

### fetch() Signature

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

### store() Signature

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

### Usage Example

```python
handler = JsonHandler()

# Fetch with type coercion
data = handler.fetch(
    path=Path("data"),
    table="users.json",
    types={'id': int, 'name': str, 'age': int, 'active': bool}
)

# Type guarantees now hold:
for row in data:
    user_id: int = row['id']      # Guaranteed to be int
    name: str = row['name']        # Guaranteed to be str
    age: int = row['age']          # Guaranteed to be int
    active: bool = row['active']   # Guaranteed to be bool

# Store with type coercion (coerces before writing)
handler.store(
    data=new_users,
    path=Path("output"),
    table="users.json",
    types={'id': int, 'name': str, 'age': int}
)
```

## Processing Order

Type coercion is applied after loading data, before other processing steps:

1. Load raw data from file
2. **Type coercion** (NEW)
3. Column selection (`cols`)
4. Filtering (`filter_`)
5. Limiting (`limit`)

## Error Handling Behavior

### When strict=True (default)
- Coercion failures raise `TypeError` immediately
- No data is returned
- Exception includes field name, value, and target type

### When strict=False
- Coercion failures skip the problematic row
- Method returns successfully with remaining rows
- No exceptions raised for coercion failures

## Implementation Structure

### New Files
- `dal/post_processing.py` - Contains `PostProcessingMixin` class with:
  - `_coerce_row()` - Type coercion for a single row
  - `_coerce_value()` - Type coercion for a single value
  - `_select_columns()` - Column selection logic
  - `_apply_processing()` - Unified post-processing pipeline

### Modified Files
- `dal/json_handler.py` - Inherit `PostProcessingMixin`, add `types` parameter, simplify by using `_apply_processing()`
- `dal/csv_handler.py` - Inherit `PostProcessingMixin`, add `types` parameter, simplify by using `_apply_processing()`
- `dal/pkl_handler.py` - Inherit `PostProcessingMixin`, add `types` parameter, simplify by using `_apply_processing()`
- `dal/xlsx_handler.py` - Inherit `PostProcessingMixin`, add `types` parameter, simplify by using `_apply_processing()`
- `dal/sqlite_handler.py` - Inherit `PostProcessingMixin`, add `types` parameter, simplify by using `_apply_processing()`

### Directory Structure
```
dal/
├── __init__.py
├── abc.py
├── post_processing.py  # NEW - PostProcessingMixin
├── json_handler.py     # Modified - inherit mixin, add types, use _apply_processing
├── csv_handler.py      # Modified - inherit mixin, add types, use _apply_processing
├── pkl_handler.py      # Modified - inherit mixin, add types, use _apply_processing
├── xlsx_handler.py     # Modified - inherit mixin, add types, use _apply_processing
└── sqlite_handler.py   # Modified - inherit mixin, add types, use _apply_processing
```

### Code Reduction Benefit

Each handler currently has ~20-30 lines of duplicated code for cols/filter_/limit processing. By consolidating into `PostProcessingMixin`, we eliminate this duplication across all 5 handlers (~100-150 lines of duplicated code).

## Testing Strategy

### Unit Tests for _coerce_value
- Valid conversions for each type (int, float, str, bool)
- `None` source values → defaults
- Invalid conversions → `TypeError`
- Edge cases: empty strings, whitespace, case-insensitive bool strings

### Unit Tests for _coerce_row
- Fields in both row and types → coerced
- Fields in row but not in types → unchanged
- Fields in types but not in row → silent skip
- Empty types dict → no changes
- Empty row → empty row

### Integration Tests
- Each handler's `fetch()` with `types` returns correctly typed data
- Each handler's `store()` with `types` coerces before storing
- Coercion failures raise `TypeError` with `strict=True`
- Coercion failures skip rows with `strict=False`
- Interaction with `cols`, `filter_`, `limit` parameters works correctly

### Test Example
```python
def test_json_handler_fetch_with_types():
    handler = JsonHandler()
    handler.store(
        [{'id': '123', 'name': 'Alice', 'age': '30'}],
        path=test_path,
        table='test.json'
    )

    result = handler.fetch(
        path=test_path,
        table='test.json',
        types={'id': int, 'name': str, 'age': int}
    )

    assert result[0]['id'] == 123
    assert isinstance(result[0]['id'], int)
    assert isinstance(result[0]['name'], str)
    assert isinstance(result[0]['age'], int)
```

## Backward Compatibility

All changes are additive:
- The `types` parameter is optional with default `None`
- When `types=None`, behavior is identical to current implementation
- Existing code continues to work without modification
- No breaking changes to existing APIs

## Edge Cases Defined

1. **Field in row, NOT in types**: Keep original value unchanged
2. **Field in types, NOT in row**: Skip silently (no error, no field added)
3. **None source value**: Convert to type-specific default (0, 0.0, "", False)
4. **Empty types dict**: No coercion applied
5. **Empty row**: Returns empty row
6. **Invalid conversion**: Raise `TypeError` (or skip row if `strict=False`)
