import pytest

from to_cei._fields import Field


def test_reraises_errors_of_other_constructors_as_their_base():
    def decode(value):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    class Probe:
        field = Field(decode)

    with pytest.raises(ValueError, match="field: .*invalid start byte"):
        Probe().field = "x"
