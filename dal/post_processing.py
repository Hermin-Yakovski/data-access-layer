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
