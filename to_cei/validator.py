from enum import Enum
from typing import Any

import xmlschema
from lxml import etree

from to_cei import config


class Schema(str, Enum):
    CEI = config.CEI_NS


class Validator:
    def __validate(self, element: etree._Element, schema: Schema) -> None:
        xsd_content = config.file_cache.get(schema.value)
        if xsd_content:
            xsd = xmlschema.XMLSchema11(xsd_content)
            resource: Any = element
            xsd.validate(resource)

    def validate_cei(self, element: etree._Element):
        return self.__validate(element, Schema.CEI)
