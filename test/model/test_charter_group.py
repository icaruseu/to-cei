import pathlib

import pytest
from lxml import etree

from model.charter import Charter
from model.charter_group import Charter_group
from model.validator import Validator


def test_is_valid_cei():
    group = Charter_group("Charter group", [Charter("1A"), Charter("1b")])
    Validator().validate_cei(group.to_xml())


def test_writes_correct_file(tmp_path):
    d = tmp_path
    group = Charter_group("Charter group", [Charter("1A"), Charter("1b")])
    group.to_file(d)
    out = pathlib.Path(d, "charter_group.cei.group.xml")
    assert out.is_file()
    written = etree.parse(str(out))
    Validator().validate_cei(written.getroot())


def test_raises_exception_for_empty_name():
    with pytest.raises(ValueError):
        Charter_group("")
