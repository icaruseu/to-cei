import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from lxml import etree

from to_cei.config import CEI_PREFIX


class XmlAssembler(ABC):
    @abstractmethod
    def to_xml(self, add_schema_location: bool = False) -> Optional[etree._Element]:
        pass

    def to_string(self, add_schema_location: bool = False) -> str:
        """Serializes the xml representation of the object to a string.

        Args:
            add_schema_location: If True, the CEI schema location is added to the root element.

        Returns:
            A string representation of the object.
        """
        xml = self.to_xml(add_schema_location)
        return (
            ""
            if xml is None
            else str(
                etree.tostring(
                    xml,
                    encoding="unicode",
                    pretty_print=True,
                )
            )
        )

    def to_file(
        self,
        name: str,
        folder: Optional[str | Path] = None,
        inclusive_ns_prefixes: List[str] = [],
        add_schema_location: bool = False,
    ):
        xml = self.to_xml(add_schema_location)
        if xml is None:
            raise Exception("Failed to read xml")
        folder = (
            folder
            if isinstance(folder, str)
            else (
                str(folder.absolute())
                if isinstance(folder, Path)
                else os.path.abspath(os.getcwd())
            )
        )
        os.makedirs(folder, exist_ok=True)
        etree.ElementTree(xml).write(
            os.path.join(folder, name + ".xml"),
            encoding="UTF-8",
            pretty_print=True,
            inclusive_ns_prefixes=[CEI_PREFIX] + inclusive_ns_prefixes,
            xml_declaration=True,
            standalone=False,
        )
