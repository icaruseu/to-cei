import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from lxml import etree

from config import CEI_PREFIX


class XmlAssembler(ABC):
    @abstractmethod
    def to_xml(self) -> Optional[etree._Element]:
        pass

    def to_string(self) -> str:
        xml = self.to_xml()
        return (
            ""
            if xml is None
            else etree.tostring(xml, encoding="unicode", pretty_print=True)
        )

    def to_file(
        self,
        name: str,
        folder: str | Path = None,
        inclusive_ns_prefixes: List[str] = [],
    ):
        print(name, folder)
        xml = self.to_xml()
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
        etree.ElementTree(xml).write(
            os.path.join(folder, name + ".xml"),
            pretty_print=True,
            inclusive_ns_prefixes=[CEI_PREFIX] + inclusive_ns_prefixes,
        )
