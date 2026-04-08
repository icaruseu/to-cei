import re
import unicodedata

from lxml import etree

from to_cei.charter import Charter
from to_cei.config import CEI, CEI_SCHEMA_LOCATION_ATTRIBUTE
from to_cei.xml_assembler import XmlAssembler


def _slugify(name: str) -> str:
    """ASCII-fold a name into a filesystem-safe filename stem."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w]+", "_", ascii_only).strip("_").lower()
    return slug or "charter_group"


class CharterGroup(XmlAssembler):
    _charters: list[Charter] | None = None
    _name: str = ""

    def __init__(self, name: str, charters: list[Charter] | None = None):
        """Creates a new charter group object.

        Args:
            name (str): The name of the charter group. Is not allowed to be empty
            charters: An optional list of Charter objects
        """
        self.name = name
        self.charters = charters

    @property
    def charters(self):
        return self._charters

    @charters.setter
    def charters(self, value: list[Charter] | None):
        self._charters = list(value) if value is not None else []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if len(value) == 0:
            raise ValueError("Group name cannot be empty")
        self._name = value

    def to_xml(self, add_schema_location: bool = False) -> etree._Element:
        """Creates an xml representation of the charter group.

        Args:
            add_schema_location: If True, the CEI schema location is added to the root element.

        Returns:
            An etree Element object representing the charter group.
        """
        cei = CEI.cei(
            CEI.teiHeader(CEI.fileDesc(CEI.titleStmt(CEI.title(self.name)))),
            CEI.text(CEI.group(*[charter.to_xml() for charter in self.charters])),
        )
        if add_schema_location:
            cei.attrib.update(CEI_SCHEMA_LOCATION_ATTRIBUTE)
        return cei

    def to_file(
        self,
        folder: str | None = None,
        add_schema_location: bool = False,
        filename: str | None = None,
    ):
        """Writes the xml representation of the charter group to a file.

        The filename is derived from `filename` if provided, otherwise
        from a Unicode-aware slug of the group name (umlauts and other
        diacritics are folded, anything that isn't a word character is
        replaced with `_`).

        Args:
            folder: The folder to write the file to. If omitted, the file
                is written to the script's working directory.
            add_schema_location: If True, the CEI schema location is added
                to the root element. Defaults to False.
            filename: Optional explicit filename stem (without the
                `.cei.group` suffix). Useful when the auto-generated slug
                is not what you want.
        """
        stem = filename if filename is not None else _slugify(self.name)
        return super().to_file(
            stem + ".cei.group",
            folder=folder,
            add_schema_location=add_schema_location,
        )
