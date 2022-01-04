from typing import Any, List

import pytest
from lxml import etree

from model.charter import (CEI, CEI_NS, CHARTER_NSS, Charter,
                           CharterContentException, join, ln, ns)
from model.validator import Validator

# --------------------------------------------------------------------#
#                          Helper functions                          #
# --------------------------------------------------------------------#


def _e(value: Any) -> List[etree._Element]:
    """Makes sure that the provided value is a List of etree._Elements."""
    if not isinstance(value, List):
        raise Exception("Not a list")
    list: List[etree._Element] = value
    return list


def _xp(charter: Charter, xpath: str) -> List[etree._Element]:
    """Evaluates an xpath on the charters xml content."""
    return _e(charter.to_xml().xpath(xpath, namespaces=CHARTER_NSS))


def _xps(charter: Charter, xpath: str) -> etree._Element:
    """Evaluates an xpath on the charters xml content, makes sure that it only has a single element and returns the element."""
    list = _xp(charter, xpath)
    assert len(list) == 1
    return list[0]


# --------------------------------------------------------------------#
#                               Tests                                #
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


def test_has_correct_base_structure():
    direct_children = _xp(Charter(id_text="1"), "/cei:text/child::*")
    assert len(direct_children) == 3
    assert ln(direct_children[0]) == "front"
    assert ln(direct_children[1]) == "body"
    assert ln(direct_children[2]) == "back"


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


def test_has_correct_text_abstract():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == abstract
    abstract_xml = _xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert abstract_xml.text == abstract


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


def test_has_correct_type():
    charter = Charter(id_text="1").to_xml()
    assert charter.get("type") == "charter"


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


def test_is_valid_charter():
    charter = Charter(
        "1307 II 22",
        abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
        abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        issuer="Konrad von Lintz",
        recipient="Heinrich, des Praitenvelders Schreiber",
        transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
    )
    Validator().validate_cei(charter.to_xml())


def test_raises_exception_for_incorrect_xml_abstract():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", abstract=incorrect_element)


def test_raises_exception_for_incorrect_xml_issuer():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", issuer=incorrect_element)


def test_raises_exception_for_incorrect_xml_recipient():
    incorrect_element = CEI.issuer("A person")
    with pytest.raises(CharterContentException):
        Charter(id_text="1", recipient=incorrect_element)


def test_raises_exception_for_missing_id():
    with pytest.raises(CharterContentException):
        Charter(id_text="")


def test_raises_exception_for_xml_abstract_with_issuer():
    with pytest.raises(CharterContentException):
        Charter(id_text="1", abstract=CEI.abstract("An abstract"), issuer="An issuer")


def test_raises_exception_for_xml_abstract_with_recipient():
    with pytest.raises(CharterContentException):
        Charter(
            id_text="1", abstract=CEI.abstract("An abstract"), recipient="An recipient"
        )
