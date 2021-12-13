from enum import Enum

import xmlschema
from lxml import etree

import config


class Schema(str, Enum):
    CEI = "https://www.monasterium.net/mom/resource/?atomid=tag:www.monasterium.net,2011:/mom/resource/xsd/cei"


class Validator:
    def __validate(self, element: etree.Element, schema: Schema) -> None:
        xsd_content = config.file_cache.get(schema.value)
        if xsd_content:
            xsd = xmlschema.XMLSchema11(xsd_content)
            xsd.validate(element)

    def validate_cei(self, element: etree.Element):
        return self.__validate(element, Schema.CEI)
