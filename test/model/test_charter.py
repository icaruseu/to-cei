from model.charter import Charter
from model.validator import Validator


def test_is_valid_charter():
    charter = Charter(
        id="1",
        abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
    )
    Validator().validate_cei(charter.to_xml())
