from pathlib import Path, PurePosixPath

import pytest
from lxml import etree

from to_cei import CEI, Charter, CharterGroup


def test_string_is_the_xml_as_built():
    charter = Charter(id_text="1", abstract="Regest")
    assert charter.to_string() == etree.tostring(charter.to_xml(), encoding="unicode")


def test_adds_no_whitespace_between_elements():
    xml = Charter(id_text="1").to_string()
    assert 'type="charter"><cei:front/><cei:body><cei:idno' in xml


def test_keeps_passed_elements_unchanged():
    seal_description = CEI.sealDesc(CEI.seal("Siegel 1"), "\n  ", CEI.seal("Siegel 2"))
    xml = Charter(id_text="1", seal_description=seal_description).to_string()
    assert (
        "<cei:sealDesc><cei:seal>Siegel 1</cei:seal>\n  "
        "<cei:seal>Siegel 2</cei:seal></cei:sealDesc>"
    ) in xml


def test_file_is_the_xml_as_built(tmp_path):
    group = CharterGroup("Gruppe", [Charter(id_text="1", abstract="Regest")])
    group.to_file(tmp_path)
    written = etree.parse(tmp_path / "gruppe.cei.group.xml").getroot()
    assert etree.tostring(written) == etree.tostring(group.to_xml())


class Folder:
    def __init__(self, name):
        self.name = name

    def __fspath__(self):
        return self.name


@pytest.mark.parametrize("make_folder", [str, Path, PurePosixPath, Folder])
def test_writes_into_any_path_type(tmp_path, monkeypatch, make_folder):
    monkeypatch.chdir(tmp_path)
    Charter(id_text="1").to_file(make_folder("sub"))
    assert (tmp_path / "sub" / "1.cei.xml").is_file()


@pytest.mark.parametrize("folder", [None, ""])
def test_writes_into_the_current_directory_by_default(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    Charter(id_text="1").to_file(folder)
    assert (tmp_path / "1.cei.xml").is_file()
