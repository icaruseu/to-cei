import pytest

from to_cei.validator import Validator


def test_no_exception_for_correct_cei(valid_cei):
    Validator().validate_cei(valid_cei)


def test_raises_exception_for_incorrect_cei(invalid_cei):
    with pytest.raises(Exception):
        Validator().validate_cei(invalid_cei)
