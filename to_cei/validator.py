"""CEI schema validation. The XSD is loaded once per `Validator` instance."""


from typing import Any

import xmlschema
from lxml import etree

from to_cei import config


class Validator:
    _schema: xmlschema.XMLSchema11

    def __init__(self) -> None:
        xsd_content = config.file_cache.get(config.CEI_NS)
        self._schema = xmlschema.XMLSchema11(xsd_content)

    def validate_cei(self, element: etree._Element) -> None:
        """Validate `element` against the CEI schema.

        Raises `xmlschema.XMLSchemaValidationError` on failure.
        """
        resource: Any = element
        self._schema.validate(resource)

    def is_valid_cei(self, element: etree._Element) -> bool:
        """Non-raising variant of `validate_cei`."""
        resource: Any = element
        return self._schema.is_valid(resource)
