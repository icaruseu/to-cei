from typing import List

import pytest
from lxml import etree

from model.charter import CEI_NS, Charter
from model.validator import Validator


def test_has_correct_base_structure():
    charter_xml = Charter(id_text="1").to_xml()
    direct_children = charter_xml.xpath(
        "/cei:text/child::*", namespaces={"cei": CEI_NS}
    )
    assert isinstance(direct_children, List)
    assert len(direct_children) == 3
    assert etree.QName(direct_children[0].tag).localname == "front"
    assert etree.QName(direct_children[1].tag).localname == "body"
    assert etree.QName(direct_children[2].tag).localname == "back"


def test_has_correct_abstract_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        abstract_bibls=bibl_text,
    ).to_xml()
    bibls = charter.xpath(
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*",
        namespaces={"cei": CEI_NS},
    )
    assert isinstance(bibls, List)
    assert len(bibls) == 1
    assert bibls[0].text == bibl_text


def test_has_correct_abstract_bibls():
    bibl_texts = ["Bibl a", "Bibl b"]
    charter = Charter(
        id_text="1",
        abstract_bibls=bibl_texts,
    ).to_xml()
    bibls = charter.xpath(
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*",
        namespaces={"cei": CEI_NS},
    )
    assert isinstance(bibls, List)
    assert len(bibls) == 2
    assert bibls[0].text == bibl_texts[0]
    assert bibls[1].text == bibl_texts[1]


def test_has_correct_id():
    id = "~!1307 II 22|23.Ⅱ"
    id_norm = "~%211307%20II%2022%7C23.%E2%85%A1"
    charter = Charter(id_text=id)
    assert charter.id_text == id
    assert charter.id_norm == id_norm
    charter_xml = charter.to_xml()
    idno = charter_xml.xpath("/cei:text/cei:body/cei:idno", namespaces={"cei": CEI_NS})
    assert isinstance(idno, List)
    assert len(idno) == 1
    assert idno[0].get("id") == id_norm
    assert idno[0].text == id


def test_has_correct_id_norm():
    id_norm = "1307_%E2%85%A1_22"
    charter = Charter(id_text="1307 Ⅱ 22", id_norm="1307_Ⅱ_22")
    assert charter.id_norm == id_norm
    charter_xml = charter.to_xml()
    idno = charter_xml.xpath("/cei:text/cei:body/cei:idno", namespaces={"cei": CEI_NS})
    assert idno[0].get("id") == id_norm


def test_has_correct_id_old():
    id_old = "123456 α"
    charter = Charter(id_text="1307 II 22", id_old=id_old)
    assert charter.id_old == id_old
    charter_xml = charter.to_xml()
    idno = charter_xml.xpath("/cei:text/cei:body/cei:idno", namespaces={"cei": CEI_NS})
    assert idno[0].get("old") == id_old


def test_has_correct_transcription_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        transcription_bibls=bibl_text,
    ).to_xml()
    bibls = charter.xpath(
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*",
        namespaces={"cei": CEI_NS},
    )
    assert isinstance(bibls, List)
    assert len(bibls) == 1
    assert bibls[0].text == bibl_text


def test_has_correct_transcription_bibls():
    bibl_texts = ["Bibl a", "Bibl b"]
    charter = Charter(
        id_text="1",
        transcription_bibls=bibl_texts,
    ).to_xml()
    bibls = charter.xpath(
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*",
        namespaces={"cei": CEI_NS},
    )
    assert isinstance(bibls, List)
    assert len(bibls) == 2
    assert bibls[0].text == bibl_texts[0]
    assert bibls[1].text == bibl_texts[1]


def test_has_correct_type():
    charter = Charter(id_text="1").to_xml()
    assert charter.get("type") == "charter"


def test_is_valid_charter():
    charter = Charter(
        id_text="1307 II 22",
        abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
    )
    Validator().validate_cei(charter.to_xml())


def test_raises_exception_for_missing_id():
    with pytest.raises(Exception):
        Charter("")
