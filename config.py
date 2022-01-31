from lxml.builder import ElementMaker  # type: ignore

from to_cei.filecache import FileCache

file_cache = FileCache()

CEI_NS: str = "http://www.monasterium.net/NS/cei"

CEI_PREFIX: str = "cei"

CHARTER_NSS = {CEI_PREFIX: CEI_NS}

CEI = ElementMaker(namespace=CEI_NS, nsmap=CHARTER_NSS)
