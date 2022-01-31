from typing import Any, List

from lxml import etree

from config import CHARTER_NSS
from to_cei.XmlAssembler import XmlAssembler


def e(value: Any) -> List[etree._Element]:
    """Makes sure that the provided value is a List of etree._Elements. Raises an exception otherwise."""
    if not isinstance(value, List):
        raise Exception("Not a list")
    list: List[etree._Element] = value
    return list


def xp(assembler: XmlAssembler, xpath: str) -> List[etree._Element]:
    """Evaluates an xpath on the charters xml content. Raises an exception if the provided assembler doesn't produce XML."""
    xml = assembler.to_xml()
    if xml is None:
        raise Exception("XML is empty")
    return e(xml.xpath(xpath, namespaces=CHARTER_NSS))


def xps(assembler: XmlAssembler, xpath: str) -> etree._Element:
    """Evaluates an xpath on the charters xml content, asserts that it only has a single element and returns the element."""
    list = xp(assembler, xpath)
    assert len(list) == 1
    return list[0]
