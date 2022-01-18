from abc import ABC, abstractmethod
from typing import Optional

from lxml import etree


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
