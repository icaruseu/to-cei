from typing import List

from lxml import etree

from model.charter import CEI_NS, Charter
from model.validator import Validator


def test_is_valid_charter():
    charter = Charter(
        id="1",
        abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
    )
    Validator().validate_cei(charter.to_xml())


def test_is_correct_base_structure():
    charter_xml = Charter(id="1").to_xml()
    direct_children = charter_xml.xpath(
        "/cei:text/child::*", namespaces={"cei": CEI_NS}
    )
    assert isinstance(direct_children, List)
    assert len(direct_children) == 3
    assert etree.QName(direct_children[0].tag).localname == "front"
    assert etree.QName(direct_children[1].tag).localname == "body"
    assert etree.QName(direct_children[2].tag).localname == "back"
