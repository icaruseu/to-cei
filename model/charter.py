from typing import List

from lxml import etree
from lxml.builder import ElementMaker

CEI_NS = "http://www.monasterium.net/NS/cei"
CEI = ElementMaker(namespace=CEI_NS, nsmap={None: CEI_NS})


class Charter:
    _abstract_bibls: List[str]
    _id: str
    _transcription_bibls: List[str]

    def __init__(
        self,
        id: str,
        abstract_bibls: str | List[str] = [],
        transcription_bibls: str | List[str] = [],
    ):
        self.abstract_bibls = abstract_bibls
        self.id = id
        self.transcription_bibls = transcription_bibls

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def abstract_bibls(self):
        return self._abstract_bibls

    @abstract_bibls.setter
    def abstract_bibls(self, value: str | List[str]):
        self._abstract_bibls = value if isinstance(value, List) else [value]

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = value

    @property
    def transcription_bibls(self):
        return self._transcription_bibls

    @transcription_bibls.setter
    def transcription_bibls(self, value: str | List[str]):
        self._transcription_bibls = value if isinstance(value, List) else [value]

    # --------------------------------------------------------------------#
    #                          Private methods                           #
    # --------------------------------------------------------------------#

    def _build(self) -> etree.Element:
        return self._create_cei_text()

    def _create_cei_back(self) -> etree.Element:
        return CEI.back()

    def _create_cei_body(self) -> etree.Element:
        return CEI.body(CEI.idno(self._id, id=self._id))

    def _create_cei_front(self) -> etree.Element:
        childs = []
        if self.abstract_bibls:
            childs.append(
                CEI.sourceDescRegest(*[CEI.bibl(bibl) for bibl in self.abstract_bibls])
            )
        if self.transcription_bibls:
            childs.append(
                CEI.sourceDescVolltext(
                    *[CEI.bibl(bibl) for bibl in self.transcription_bibls]
                )
            )
        if childs:
            source_desc = CEI.sourceDesc(*childs)
            return CEI.front(source_desc)
        else:
            return CEI.front()

    def _create_cei_text(self) -> etree.Element:
        return CEI.text(
            self._create_cei_front(),
            self._create_cei_body(),
            self._create_cei_back(),
            id=self._id,
            type="charter",
        )

    # --------------------------------------------------------------------#
    #                           Public methods                           #
    # --------------------------------------------------------------------#

    def to_string(self) -> str:
        return etree.tostring(self._build(), encoding="unicode", pretty_print=True)

    def to_xml(self) -> etree.Element:
        return self._build()
