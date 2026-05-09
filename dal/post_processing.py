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
