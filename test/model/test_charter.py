from datetime import datetime
from typing import Any, List

import pytest
from astropy.time.core import Time
from lxml import etree

from model.charter import (CEI, CEI_NS, CHARTER_NSS, NO_DATE_TEXT,
                           NO_DATE_VALUE, Charter, CharterContentException,
                           join, ln, ns)
from model.validator import Validator

# --------------------------------------------------------------------#
#                          Helper functions                          #
# --------------------------------------------------------------------#


def _e(value: Any) -> List[etree._Element]:
    """Makes sure that the provided value is a List of etree._Elements. Raises an exception otherwise."""
    if not isinstance(value, List):
        raise Exception("Not a list")
    list: List[etree._Element] = value
    return list


def _xp(charter: Charter, xpath: str) -> List[etree._Element]:
    """Evaluates an xpath on the charters xml content."""
    return _e(charter.to_xml().xpath(xpath, namespaces=CHARTER_NSS))


def _xps(charter: Charter, xpath: str) -> etree._Element:
    """Evaluates an xpath on the charters xml content, asserts that it only has a single element and returns the element."""
    list = _xp(charter, xpath)
    assert len(list) == 1
    return list[0]


# --------------------------------------------------------------------#
#                               Tests                                #
# --------------------------------------------------------------------#


# --------------------------------------------------------------------#
#                          Helper functions                          #
# --------------------------------------------------------------------#


def test_gets_correct_local_name():
    assert ln(CEI.text()) == "text"


def test_gets_correct_namespace():
    assert ns(CEI.text()) == CEI_NS


def test_joins_correctly():
    joined = join(CEI.text(), None, CEI.persName(), None)
    assert len(joined) == 2
    assert etree.tostring(joined[0]) == etree.tostring(CEI.text())
    assert etree.tostring(joined[1]) == etree.tostring(CEI.persName())


# --------------------------------------------------------------------#
#                         Charter as a whole                         #
# --------------------------------------------------------------------#


def test_has_correct_base_structure():
    direct_children = _xp(Charter(id_text="1"), "/cei:text/child::*")
    assert len(direct_children) == 3
    assert ln(direct_children[0]) == "front"
    assert ln(direct_children[1]) == "body"
    assert ln(direct_children[2]) == "back"


def test_is_valid_charter():
    charter = Charter(
        "1307 II 22",
        abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
        abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        date="1307 II 22",
        date_value=Time("1307-02-22", format="isot", scale="ut1"),
        issued_place="Wiener",
        issuer="Konrad von Lintz",
        recipient="Heinrich, des Praitenvelders Schreiber",
        tradition_form="orig.",
        transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
    )
    Validator().validate_cei(charter.to_xml())


# --------------------------------------------------------------------#
#                          Charter abstract                          #
# --------------------------------------------------------------------#


def test_has_correct_text_abstract():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == abstract
    abstract_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert abstract_xml.text == abstract


def test_has_correct_xml_abstract():
    pers_name = "Konrad von Lintz"
    abstract = CEI.abstract(
        CEI.persName(pers_name),
        ", Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag.",
    )
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == abstract
    abstract_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert abstract_xml.text == abstract.text
    pers_name_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:persName"
    )
    assert pers_name_xml.text == pers_name


def test_raises_exception_for_incorrect_xml_abstract():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", abstract=incorrect_element)


# --------------------------------------------------------------------#
#                           Bibliographies                           #
# --------------------------------------------------------------------#


def test_has_correct_abstract_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        abstract_bibls=bibl_text,
    )
    assert isinstance(charter.abstract_bibls, List)
    bibl = _xps(charter, "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*")
    assert bibl.text == bibl_text


def test_has_correct_abstract_bibls():
    bibl_texts = ["Bibl a", "Bibl b"]
    bibls = _xp(
        Charter(
            id_text="1",
            abstract_bibls=bibl_texts,
        ),
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*",
    )
    assert len(bibls) == 2
    assert bibls[0].text == bibl_texts[0]
    assert bibls[1].text == bibl_texts[1]


def test_has_correct_transcription_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        transcription_bibls=bibl_text,
    )
    assert isinstance(charter.transcription_bibls, List)
    bibls = _xps(charter, "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*")
    assert bibls.text == bibl_text


def test_has_correct_transcription_bibls():
    bibl_texts = ["Bibl a", "Bibl b"]
    bibls = _xp(
        Charter(
            id_text="1",
            transcription_bibls=bibl_texts,
        ),
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*",
    )
    assert len(bibls) == 2
    assert bibls[0].text == bibl_texts[0]
    assert bibls[1].text == bibl_texts[1]


# --------------------------------------------------------------------#
#                            Charter date                             #
# --------------------------------------------------------------------#


def test_has_correct_date_range_with_99999999():
    charter = Charter(id_text="1", date="unknown", date_value=("99999999", "99999999"))
    assert charter.date == "unknown"
    assert charter.date_value == None
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "unknown"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_date_with_99999999():
    charter = Charter(id_text="1", date="unknown", date_value="99999999")
    assert charter.date == "unknown"
    assert charter.date_value == None
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "unknown"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_date_range_with_datetime():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(datetime(1300, 1, 1), datetime(1300, 12, 31)),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_datetime():
    charter = Charter(
        id_text="1",
        date="1. 1. 1300",
        date_value=datetime(1300, 1, 1),
    )
    assert charter.date == "1. 1. 1300"
    assert charter.date_value == Time("1300-01-01", format="isot", scale="ut1")
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_date_range_with_iso():
    charter = Charter(id_text="1", date="1300", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_iso():
    charter = Charter(id_text="1", date="12. 1. 1342", date_value="1342-01-12")
    assert charter.date == "12. 1. 1342"
    assert charter.date_value == Time("1342-01-12", format="isot", scale="ut1")
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "12. 1. 1342"
    assert date_xml.get("value") == "13420112"


def test_has_correct_date_range_with_Time():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(
            Time({"year": 1300, "month": 1, "day": 1}, scale="ut1"),
            Time({"year": 1300, "month": 12, "day": 31}, scale="ut1"),
        ),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_Time():
    charter = Charter(
        id_text="1",
        date="1. 1. 1300",
        date_value=Time({"year": 1300, "month": 1, "day": 1}, scale="ut1"),
    )
    assert charter.date == "1. 1. 1300"
    assert charter.date_value == Time("1300-01-01", format="isot", scale="ut1")
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_empty_date():
    charter = Charter(id_text="1")
    assert charter.date == None
    assert charter.date_value == None
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == NO_DATE_TEXT
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_empty_date_range_text():
    charter = Charter(id_text="1", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == None
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "+01300-01-01 - +01300-12-31"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_empty_date_text():
    charter = Charter(id_text="1", date_value="1342-01-12")
    assert charter.date == None
    assert charter.date_value == Time("1342-01-12", format="isot", scale="ut1")
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "+01342-01-12"
    assert date_xml.get("value") == "13420112"


def test_has_correct_empty_date_value():
    text = "Sine dato"
    charter = Charter(id_text="1", date=text)
    assert charter.date == text
    assert charter.date_value == None
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == text
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_xml_date():
    date_text = "12. 10. 1789"
    date_value = "17980101"
    date = CEI.date(date_text, {"value": date_value})
    charter = Charter(id_text="1", date=date)
    assert charter.date == date
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == date_text
    assert date_xml.get("value") == date_value


def test_has_correct_xml_date_range():
    date_text = "some time in 1789"
    date_from = "17980101"
    date_to = "17981231"
    date = CEI.dateRange(date_text, {"from": date_from, "to": date_to})
    charter = Charter(id_text="1", date=date)
    assert charter.date == date
    date_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == date_text
    assert date_xml.get("from") == date_from
    assert date_xml.get("to") == date_to


def test_raises_exception_when_initializing_with_xml_date_and_value():
    date_value = "17980101"
    date = CEI.date("12. 10. 1789", {"value": date_value})
    with pytest.raises(CharterContentException):
        Charter(id_text="1", date=date, date_value=date_value)


def test_raises_exception_for_incorrect_date_value():
    with pytest.raises(CharterContentException):
        Charter(
            id_text="1",
            date="in 1789",
            date_value=("17980101", datetime(1789, 12, 31)),
        )


def test_raises_exception_for_incorrect_xml_date():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", date=incorrect_element)


def test_raises_exception_when_setting_date_value_for_xml_date():
    date_from = "17980101"
    date_to = "17981231"
    date = CEI.dateRange("12. 10. 1789", {"from": date_from, "to": date_to})
    charter = Charter(id_text="1", date=date)
    with pytest.raises(CharterContentException):
        charter.date_value = (date_from, date_to)


# --------------------------------------------------------------------#
#                             Charter id                             #
# --------------------------------------------------------------------#


def test_has_correct_id():
    id_text = "~!1307 II 22|23.Ⅱ"
    id_norm = "~%211307%20II%2022%7C23.%E2%85%A1"
    charter = Charter(id_text=id_text)
    assert charter.id_text == id_text
    assert charter.id_norm == id_norm
    idno = _xps(charter, "/cei:text/cei:body/cei:idno")
    assert idno.get("id") == id_norm
    assert idno.text == id_text


def test_has_correct_id_norm():
    id_text = "1307 Ⅱ 22"
    id_norm = "1307_%E2%85%A1_22"
    charter = Charter(id_text=id_text, id_norm="1307_Ⅱ_22")
    assert charter.id_text == id_text
    assert charter.id_norm == id_norm
    idno = _xps(charter, "/cei:text/cei:body/cei:idno")
    assert idno.get("id") == id_norm
    assert idno.text == id_text


def test_has_correct_id_old():
    id_old = "123456 α"
    idno = _xps(
        Charter(id_text="1307 II 22", id_old=id_old), "/cei:text/cei:body/cei:idno"
    )
    assert idno.get("old") == id_old


def test_raises_exception_for_missing_id():
    with pytest.raises(CharterContentException):
        Charter(id_text="")


# --------------------------------------------------------------------#
#                        Charter issued place                        #
# --------------------------------------------------------------------#


def test_has_correct_text_issued_place():
    issued_place = "Wien"
    charter = Charter(id_text="1", issued_place=issued_place)
    assert charter.issued_place == issued_place
    issued_place_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:placeName"
    )
    assert issued_place_xml.text == issued_place


def test_has_correct_xml_issued_place():
    issued_place = CEI.placeName("Wien")
    charter = Charter(id_text="1", issued_place=issued_place)
    assert charter.issued_place == issued_place
    issued_place_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:placeName"
    )
    assert issued_place_xml.text == issued_place.text


def test_raises_exception_for_incorrect_xml_issued_place():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", issued_place=incorrect_element)


# --------------------------------------------------------------------#
#                           Charter issuer                           #
# --------------------------------------------------------------------#


def test_has_correct_abstract_with_text_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = "Konrad von Lintz"
    charter = Charter(id_text="1", abstract=abstract, issuer=issuer)
    assert isinstance(charter.issuer, str)
    assert charter.issuer == issuer
    issuer_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer


def test_has_correct_abstract_with_xml_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = CEI.issuer("Konrad von Lintz")
    assert isinstance(issuer, etree._Element)
    charter = Charter(id_text="1", abstract=abstract, issuer=issuer)
    assert isinstance(charter.issuer, etree._Element)
    assert charter.issuer.text == issuer.text
    issuer_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer.text


def test_raises_exception_for_incorrect_xml_issuer():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", issuer=incorrect_element)


def test_raises_exception_for_xml_abstract_with_issuer():
    with pytest.raises(CharterContentException):
        Charter(id_text="1", abstract=CEI.abstract("An abstract"), issuer="An issuer")


# --------------------------------------------------------------------#
#                         Charter recipient                          #
# --------------------------------------------------------------------#


def test_has_correct_abstract_with_text_recipient():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    recipient = "Heinrich Müller"
    charter = Charter(id_text="1", abstract=abstract, recipient=recipient)
    assert isinstance(charter.recipient, str)
    assert charter.recipient == recipient
    recipient_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:recipient"
    )
    assert recipient_xml.text == recipient


def test_has_correct_abstract_with_xml_recipient():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    recipient = CEI.recipient("Heinrich Müller")
    assert isinstance(recipient, etree._Element)
    charter = Charter(id_text="1", abstract=abstract, recipient=recipient)
    assert isinstance(charter.recipient, etree._Element)
    assert charter.recipient.text == recipient.text
    recipient_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:recipient"
    )
    assert recipient_xml.text == recipient.text


def test_raises_exception_for_xml_abstract_with_recipient():
    with pytest.raises(CharterContentException):
        Charter(
            id_text="1", abstract=CEI.abstract("An abstract"), recipient="An recipient"
        )


def test_raises_exception_for_incorrect_xml_recipient():
    incorrect_element = CEI.issuer("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", recipient=incorrect_element)


# --------------------------------------------------------------------#
#                       Charter tradition form                       #
# --------------------------------------------------------------------#


def test_has_correct_tradition_form():
    tradition_form = "orig."
    charter = Charter(id_text="1", tradition_form=tradition_form)
    assert charter.tradition_form == tradition_form
    tradition_form_xml = _xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:traditioForm"
    )
    assert tradition_form_xml.text == tradition_form


# --------------------------------------------------------------------#
#                            Charter type                            #
# --------------------------------------------------------------------#


def test_has_correct_type():
    charter = Charter(id_text="1").to_xml()
    assert charter.get("type") == "charter"
