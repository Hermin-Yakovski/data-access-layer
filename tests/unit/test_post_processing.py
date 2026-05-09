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
        with pytest.raises(TypeError, match="Cannot convert int value '123' to list"):
            mixin._coerce_value(123, list)
