import pathlib

import pytest
from lxml import etree

from to_cei.charter import Charter
from to_cei.charter_group import CharterGroup
from to_cei.config import CEI, SCHEMA_LOCATION, SCHEMA_LOCATION_QNAME
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


def test_charters_are_not_shared_between_instances():
    g1 = CharterGroup("g1")
    g1.charters.append(Charter("a"))
    g2 = CharterGroup("g2")
    assert g2.charters == []


def test_filename_slug_handles_umlauts(tmp_path):
    group = CharterGroup("Schöne Gruppe", [Charter("1")])
    group.to_file(tmp_path)
    assert pathlib.Path(tmp_path, "schone_gruppe.cei.group.xml").is_file()


def test_filename_slug_handles_punctuation(tmp_path):
    group = CharterGroup("St. Veit a. d. Glan", [Charter("1")])
    group.to_file(tmp_path)
    assert pathlib.Path(tmp_path, "st_veit_a_d_glan.cei.group.xml").is_file()


def test_filename_explicit_override(tmp_path):
    group = CharterGroup("Whatever", [Charter("1")])
    group.to_file(tmp_path, filename="custom_name")
    assert pathlib.Path(tmp_path, "custom_name.cei.group.xml").is_file()


def test_raises_exception_for_duplicate_id_norm():
    group = CharterGroup(
        "Série K",
        [
            Charter("K//5, n° 4/2"),
            Charter("K//5, n° 4/2"),
            Charter("K//5, n° 4/2", id_norm="K//5, n° 4/2 b"),
        ],
    )
    with pytest.raises(ValueError, match=r"K\|\|5_n°_4\|2$"):
        group.to_xml()


def test_duplicate_check_compares_mom_ids():
    group = CharterGroup("Gruppe", [Charter("1307 II 22"), Charter("1307_II_22")])
    with pytest.raises(ValueError, match="1307_II_22"):
        group.to_xml()


@pytest.mark.parametrize("name", [None, 5, CEI.title("Gruppe")])
def test_raises_type_error_for_a_name_that_is_not_text(name):
    with pytest.raises(TypeError, match="name"):
        CharterGroup(name)


def test_accepts_a_single_charter():
    assert len(CharterGroup("Gruppe", Charter("1")).charters) == 1


@pytest.mark.parametrize("charters", ["1", ["1"], [Charter("1"), None]])
def test_raises_type_error_for_entries_that_are_not_charters(charters):
    with pytest.raises(TypeError, match="charters"):
        CharterGroup("Gruppe", charters)


def test_checks_charters_appended_in_place():
    group = CharterGroup("Gruppe", Charter("1"))
    group.charters.append("2")  # pyright: ignore[reportArgumentType]
    with pytest.raises(TypeError, match="charters"):
        group.to_xml()
