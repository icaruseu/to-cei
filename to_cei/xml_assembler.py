import os
from abc import ABC, abstractmethod
from pathlib import Path

from lxml import etree


class XmlAssembler(ABC):
    @abstractmethod
    def to_xml(self, add_schema_location: bool = False) -> etree._Element:
        pass

    def to_string(self, add_schema_location: bool = False) -> str:
        """Serializes the xml representation of the object to a string.

        Args:
            add_schema_location: If True, the CEI schema location is added to
                the root element.

        Returns:
            A string representation of the object.
        """
        return etree.tostring(self.to_xml(add_schema_location), encoding="unicode")

    def _write_file(
        self,
        name: str,
        folder: str | os.PathLike[str] | None = None,
        add_schema_location: bool = False,
    ) -> None:
        directory = Path(folder or ".")
        directory.mkdir(parents=True, exist_ok=True)
        etree.ElementTree(self.to_xml(add_schema_location)).write(
            directory / (name + ".xml"),
            encoding="UTF-8",
            xml_declaration=True,
            standalone=False,
        )
