import os
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence

from lxml import etree

from to_cei._fields import Field, check_fields
from to_cei.charter import Charter
from to_cei.config import CEI, CEI_SCHEMA_LOCATION_ATTRIBUTE
from to_cei.helpers import required_text
from to_cei.xml_assembler import XmlAssembler


def _slugify(name: str) -> str:
    """ASCII-fold a name into a filesystem-safe filename stem."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w]+", "_", ascii_only).strip("_").lower()
    return slug or "charter_group"


def _norm_charters(value: Charter | Sequence[Charter] | None) -> list[Charter]:
    if value is None:
        return []
    if isinstance(value, Charter):
        return [value]
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise TypeError(f"expected a Charter or a sequence, got {type(value).__name__}")
    for entry in value:
        if not isinstance(entry, Charter):
            raise TypeError(f"expected a Charter, got {type(entry).__name__}")
    return list(value)


class CharterGroup(XmlAssembler):
    charters: Field[list[Charter]] = Field(_norm_charters)
    name: Field[str] = Field(required_text)

    def __init__(
        self, name: str, charters: Charter | Sequence[Charter] | None = None
    ) -> None:
        """A group of charters, written as one `cei:cei` document.

        Args:
            name: The name of the charter group. It must not be empty.
            charters: One `Charter` or a sequence of them.

        Raises:
            TypeError: if `name` isn't text or a charter isn't a `Charter`.
            ValueError: if `name` is empty.
        """
        self.name = name
        self.charters = charters

    def to_xml(self, add_schema_location: bool = False) -> etree._Element:
        """Creates an xml representation of the charter group.

        Args:
            add_schema_location: If True, the CEI schema location is added to
                the root element.

        Returns:
            An etree Element object representing the charter group.

        Raises:
            TypeError: if an entry added to `charters` in place isn't a
                `Charter`.
            ValueError: if several charters have the same `id_norm`.
        """
        check_fields(self)
        ids = Counter(charter.id_norm for charter in self.charters)
        duplicates = sorted(id_norm for id_norm, count in ids.items() if count > 1)
        if duplicates:
            raise ValueError(
                f"Several charters have the same id_norm: {', '.join(duplicates)}"
            )
        cei = CEI.cei(
            CEI.teiHeader(CEI.fileDesc(CEI.titleStmt(CEI.title(self.name)))),
            CEI.text(CEI.group(*[charter.to_xml() for charter in self.charters])),
        )
        if add_schema_location:
            cei.attrib.update(CEI_SCHEMA_LOCATION_ATTRIBUTE)
        return cei

    def to_file(
        self,
        folder: str | os.PathLike[str] | None = None,
        add_schema_location: bool = False,
        filename: str | None = None,
    ):
        """Writes the xml representation of the charter group to a file.

        The filename is derived from `filename` if provided, otherwise
        from the group name, lowercased and folded to ASCII. Characters
        without an ASCII form are dropped, each run of other non-word
        characters becomes `_`, and `_` at either end is dropped. An empty
        result becomes `charter_group`.

        Args:
            folder: The folder to write the file to. If omitted, the file
                is written to the current working directory.
            add_schema_location: If True, the CEI schema location is added
                to the root element. Defaults to False.
            filename: Optional explicit filename stem (without the
                `.cei.group.xml` suffix).
        """
        stem = filename if filename is not None else _slugify(self.name)
        self._write_file(
            stem + ".cei.group",
            folder=folder,
            add_schema_location=add_schema_location,
        )
