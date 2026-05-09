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

    def _select_columns(self, row: Dict[str, Any], cols: Set[str]) -> Dict[str, Any]:
        """Select specified columns from a row.

        Args:
            row: The row dictionary
            cols: Set of column names to select

        Returns:
            A new dictionary with only the specified columns
        """
        return {k: v for k, v in row.items() if k in cols}

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
