from lxml import etree
from lxml.builder import ElementMaker

CEI_NS: str = "http://www.monasterium.net/NS/cei"

CEI_SCHEMA_URL: str = "https://raw.githubusercontent.com/icaruseu/mom-ca/master/my/XRX/src/mom/app/cei/xsd/cei.xsd"

CEI_PREFIX: str = "cei"

CHARTER_NSS = {
    CEI_PREFIX: CEI_NS,
}

SCHEMA_LOCATION_QNAME = etree.QName(
    "http://www.w3.org/2001/XMLSchema-instance", "schemaLocation"
)

SCHEMA_LOCATION = f"{CEI_NS} {CEI_NS}"

CEI_SCHEMA_LOCATION_ATTRIBUTE = {SCHEMA_LOCATION_QNAME: SCHEMA_LOCATION}


CEI = ElementMaker(namespace=CEI_NS, nsmap=CHARTER_NSS)
