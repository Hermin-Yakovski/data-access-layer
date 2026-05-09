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
