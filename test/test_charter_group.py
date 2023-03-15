import pathlib

import pytest
from lxml import etree

from to_cei.charter import Charter
from to_cei.charter_group import CharterGroup
from to_cei.config import SCHEMA_LOCATION, SCHEMA_LOCATION_QNAME
from to_cei.validator import Validator


def test_is_valid_cei():
    group = CharterGroup("Charter group", [Charter("1A"), Charter("1b")])
    Validator().validate_cei(group.to_xml())


def test_writes_correct_file(tmp_path):
    d = tmp_path
    group = CharterGroup("Charter group", [Charter("1A"), Charter("1b")])
    group.to_file(d)
    out = pathlib.Path(d, "charter_group.cei.group.xml")
    assert out.is_file()
    written = etree.parse(str(out))
    Validator().validate_cei(written.getroot())


def test_add_schema_location_is_respected():
    group = CharterGroup("Charter group", [Charter("1A"), Charter("1b")])
    assert (
        group.to_xml(add_schema_location=True).get(SCHEMA_LOCATION_QNAME)
        == SCHEMA_LOCATION
    )
    assert group.to_xml(add_schema_location=False).get(SCHEMA_LOCATION_QNAME) == None


def test_raises_exception_for_empty_name():
    with pytest.raises(ValueError):
        CharterGroup("")
