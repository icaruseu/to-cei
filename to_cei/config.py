from lxml.builder import ElementMaker  # type: ignore

from to_cei import filecache

file_cache = filecache.FileCache()

CEI_NS: str = "http://www.monasterium.net/NS/cei"

CEI_PREFIX: str = "cei"

CHARTER_NSS = {CEI_PREFIX: CEI_NS}

CEI = ElementMaker(namespace=CEI_NS, nsmap=CHARTER_NSS)
