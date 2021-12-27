from typing import List, Optional
from urllib.parse import quote

from lxml import etree
from lxml.builder import ElementMaker

CEI_NS = "http://www.monasterium.net/NS/cei"
CEI = ElementMaker(namespace=CEI_NS, nsmap={None: CEI_NS})


class Charter:
    _abstract_bibls: List[str]
    _id_norm: str
    _id_old: Optional[str]
    _id_text: str
    _transcription_bibls: List[str]

    def __init__(
        self,
        id_text: str,
        abstract_bibls: str | List[str] = [],
        id_norm: Optional[str] = None,
        id_old: Optional[str] = None,
        transcription_bibls: str | List[str] = [],
    ):
        if not id_text:
            raise Exception("id_text is not allowed to be empty")
        self.abstract_bibls = abstract_bibls
        self.id_norm = id_norm if id_norm else id_text
        self.id_old = id_old
        self.id_text = id_text
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
    def id_norm(self):
        return self._id_norm

    @id_norm.setter
    def id_norm(self, value: str):
        self._id_norm = quote(value)

    @property
    def id_old(self):
        return self._id_old

    @id_old.setter
    def id_old(self, value: Optional[str]):
        self._id_old = value

    @property
    def id_text(self):
        return self._id_text

    @id_text.setter
    def id_text(self, value: str):
        self._id_text = value

    @property
    def transcription_bibls(self):
        return self._transcription_bibls

    @transcription_bibls.setter
    def transcription_bibls(self, value: str | List[str]):
        self._transcription_bibls = value if isinstance(value, List) else [value]

    # --------------------------------------------------------------------#
    #                        Private CEI creators                        #
    # --------------------------------------------------------------------#

    def _create_cei_back(self) -> etree.Element:
        return CEI.back()

    def _create_cei_body(self) -> etree.Element:
        children = [self._create_cei_idno]
        return CEI.body(*children)

    def _create_cei_front(self) -> etree.Element:
        children = []
        source_desc = self._create_cei_source_desc()
        if len(source_desc):
            children.append(source_desc)
        return CEI.front(*children)

    def _create_cei_idno(self) -> etree.Element:
        attributes = {"id": self.id_norm}
        if self.id_old:
            attributes["old"] = self.id_old
        return CEI.idno(self.id_text, **attributes)

    def _create_cei_source_desc(self) -> etree.Element:
        children = []
        if self.abstract_bibls:
            children.append(
                CEI.sourceDescRegest(*[CEI.bibl(bibl) for bibl in self.abstract_bibls])
            )
        if self.transcription_bibls:
            children.append(
                CEI.sourceDescVolltext(
                    *[CEI.bibl(bibl) for bibl in self.transcription_bibls]
                )
            )
        return CEI.sourceDesc(*children)

    def _create_cei_text(self) -> etree.Element:
        return CEI.text(
            self._create_cei_front(),
            self._create_cei_body(),
            self._create_cei_back(),
            type="charter",
        )

    # --------------------------------------------------------------------#
    #                          Private methods                           #
    # --------------------------------------------------------------------#

    def _build(self) -> etree.Element:
        return self._create_cei_text()

    # --------------------------------------------------------------------#
    #                           Public methods                           #
    # --------------------------------------------------------------------#

    def to_string(self) -> str:
        return etree.tostring(self._build(), encoding="unicode", pretty_print=True)

    def to_xml(self) -> etree.Element:
        return self._build()
