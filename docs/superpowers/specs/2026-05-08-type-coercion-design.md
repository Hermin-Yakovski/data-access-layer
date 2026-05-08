# Type Coercion Design

**Date:** 2026-05-08
**Author:** Brainstorming Session
**Status:** Approved

## Overview

Add automatic type coercion to the data access layer, allowing users to specify expected types for columns that will be applied during `fetch()` and `store()` operations. This eliminates the need for manual type casting and provides type guarantees at runtime.

## Problem Statement

Currently, when fetching data, users must explicitly cast values to ensure type safety:

```python
for row in handler.fetch(...):
    index: int = row['id']  # No guarantee row['id'] is actually an int
    # Explicit casting required: index = int(row['id'])
```

This is error-prone and inelegant. Type coercion should be handled transparently by the data layer.

## Requirements

1. Add type coercion to both `fetch()` and `store()` methods
2. Define expected types via a per-call `types` parameter (e.g., `{'id': int, 'name': str}`)
3. Support basic types: `int`, `float`, `str`, `bool`
4. Handle `None` source values by converting to defaults (0, 0.0, "", False)
5. Raise `TypeError` on coercion failure when `strict=True`
6. Maintain backward compatibility (optional parameter, default behavior unchanged)

## Architecture

### TypeCoercionMixin

A new mixin class providing centralized coercion logic:

```python
class TypeCoercionMixin:
    """Provides type coercion capabilities for data handlers."""

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
```

### Handler Integration

All handlers inherit from both `TypeCoercionMixin` and `DataHandler`:

```python
class JsonHandler(TypeCoercionMixin, DataHandler):
    def fetch(self, ..., types: Optional[Dict[str, Type]] = None):
        # Load data
        data = self._load_from_file()

        # Apply type coercion if types specified
        if types is not None:
            data = [self._coerce_row(row, types) for row in data]

        # Continue with existing processing
        ...
```

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
- `dal/type_coercion.py` - Contains `TypeCoercionMixin` class

### Modified Files
- `dal/json_handler.py` - Inherit mixin, add `types` parameter
- `dal/csv_handler.py` - Inherit mixin, add `types` parameter
- `dal/pkl_handler.py` - Inherit mixin, add `types` parameter
- `dal/xlsx_handler.py` - Inherit mixin, add `types` parameter
- `dal/sqlite_handler.py` - Inherit mixin, add `types` parameter

### Directory Structure
```
dal/
├── __init__.py
├── abc.py
├── type_coercion.py  # NEW
├── json_handler.py   # Modified
├── csv_handler.py    # Modified
├── pkl_handler.py    # Modified
├── xlsx_handler.py   # Modified
└── sqlite_handler.py # Modified
```

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
