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
