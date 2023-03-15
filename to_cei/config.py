from lxml import etree
from lxml.builder import ElementMaker  # type: ignore

from to_cei import filecache

file_cache = filecache.FileCache()

CEI_NS: str = "http://www.monasterium.net/NS/cei"

CEI_PREFIX: str = "cei"

CHARTER_NSS = {
    CEI_PREFIX: CEI_NS,
}

SCHEMA_LOCATION_QNAME = etree.QName(
    "http://www.w3.org/2001/XMLSchema-instance", "schemaLocation"
)

SCHEMA_LOCATION = f"{CEI_NS} {CEI_NS}"

CEI_SCHEMA_LOCATION_ATTRIBUTE = {SCHEMA_LOCATION_QNAME: SCHEMA_LOCATION}

XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


CEI = ElementMaker(namespace=CEI_NS, nsmap=CHARTER_NSS)
