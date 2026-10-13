from typing import cast

from lxml import etree

from to_cei.config import CHARTER_NSS
from to_cei.seal import Seal
from to_cei.xml_assembler import XmlAssembler


def xp(assembler: XmlAssembler | Seal, xpath: str) -> list[etree._Element]:
    """Evaluates `xpath` on the XML of `assembler`."""
    xml = assembler.to_xml()
    assert xml is not None
    elements = xml.xpath(xpath, namespaces=CHARTER_NSS)
    assert isinstance(elements, list)
    assert all(isinstance(element, etree._Element) for element in elements)
    return cast(list[etree._Element], elements)


def xps(assembler: XmlAssembler | Seal, xpath: str) -> etree._Element:
    """Like `xp`, but asserts a single match and returns it."""
    elements = xp(assembler, xpath)
    assert len(elements) == 1
    return elements[0]
