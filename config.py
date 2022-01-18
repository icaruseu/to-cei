from lxml.builder import ElementMaker  # type: ignore

from model.filecache import FileCache

file_cache = FileCache()

CEI_NS: str = "http://www.monasterium.net/NS/cei"

CHARTER_NSS = {"cei": CEI_NS}

CEI = ElementMaker(namespace=CEI_NS, nsmap=CHARTER_NSS)
