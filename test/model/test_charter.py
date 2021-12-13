from model.charter import Charter
from model.validator import Validator


def test_is_valid_charter():
    charter = Charter(id="1")
    Validator().validate_cei(charter.to_xml())
