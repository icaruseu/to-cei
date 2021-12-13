from lxml import etree
from lxml.builder import ElementMaker

CEI_XSD_URL = "https://www.monasterium.net/mom/resource/?atomid=tag:www.monasterium.net,2011:/mom/resource/xsd/cei"

CEI_NS = "http://www.monasterium.net/NS/cei"
CEI = ElementMaker(namespace=CEI_NS, nsmap={None: CEI_NS})


class Charter:
    id: str
    __root: etree.Element

    def __init__(self, id: str):
        self.id = id
        self.__root = self.__build()

    def __build(self) -> etree.Element:
        return self.__create_cei_text()

    def __create_cei_body(self) -> etree.Element:
        return CEI.body(CEI.idno(self.id, id=self.id))

    def __create_cei_front(self) -> etree.Element:
        return CEI.front()

    def __create_cei_text(self) -> etree.Element:
        return CEI.text(
            self.__create_cei_front(),
            self.__create_cei_body(),
            id=self.id,
            type="charter",
        )

    def to_xml(self) -> etree.Element:
        return self.__root

    def to_string(self) -> str:
        return etree.tostring(self.__build(), encoding="unicode", pretty_print=True)
