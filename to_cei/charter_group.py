from typing import List

from lxml import etree

from to_cei.charter import Charter
from to_cei.config import CEI
from to_cei.xml_assembler import XmlAssembler


class CharterGroup(XmlAssembler):
    _charters: List[Charter] = []
    _name: str = ""

    def __init__(self, name: str, charters: List[Charter] = []):
        """Creates a new charter group object.

        Args:
            name (str): The name of the charter group. Is not allowed to be empty
            charters(List[Charter] = []): An optional list of Charter objects
        """
        self.name = name
        self.charters = charters

    @property
    def charters(self):
        return self._charters

    @charters.setter
    def charters(self, value: List[Charter]):
        self._charters = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if len(value) == 0:
            raise ValueError("Group name cannot be empty")
        self._name = value

    def to_xml(self) -> etree._Element:
        xml = CEI.cei(
            CEI.teiHeader(CEI.fileDesc(CEI.titleStmt(CEI.title(self.name)))),
            CEI.text(CEI.group(*[charter.to_xml() for charter in self.charters])),
        )
        return xml

    def to_file(self, folder: str = None):
        return super(CharterGroup, self).to_file(
            self.name.lower().replace(" ", "_") + ".cei.group", folder=folder
        )
