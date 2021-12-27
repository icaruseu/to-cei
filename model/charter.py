from typing import List, Optional
from urllib.parse import quote

from lxml import etree
from lxml.builder import ElementMaker  # type: ignore

CEI_NS: str = "http://www.monasterium.net/NS/cei"
CEI = ElementMaker(namespace=CEI_NS, nsmap={None: CEI_NS})
CHARTER_NSS = {"cei": CEI_NS}


def join(*values: Optional[etree._Element]):
    """Joins all non-empty values in a list."""
    return [value for value in values if isinstance(value, etree._Element)]


def ln(element: etree._Element) -> str:
    """Get the local name of an element."""
    return etree.QName(element.tag).localname


def ns(element: etree._Element) -> str:
    """Get the namespace of an element."""
    return etree.QName(element.tag).namespace


class CharterContentException(Exception):
    pass


class Charter:
    _abstract: Optional[str | etree._Element]
    _abstract_bibls: List[str]
    _id_norm: str
    _id_old: Optional[str]
    _id_text: str
    _transcription_bibls: List[str]

    def __init__(
        self,
        id_text: str,
        abstract: Optional[str | etree._Element] = None,
        abstract_bibls: str | List[str] = [],
        id_norm: Optional[str] = None,
        id_old: Optional[str] = None,
        transcription_bibls: str | List[str] = [],
    ) -> None:
        """
        Creates a new charter object.

        Parameters:
        ----------
        id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.

        abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.

        abstract_bibls: The bibliography source or sources for the abstract.

        id_norm: A normalized id for the charter. It will be percent-encoded to ensure only valid characters are used. If it is ommitted, the normalized version of id_text will be used.

        id_old: An old, now obsolete identifier of the charter.

        transcription_bibls: The bibliography source or sources for the transcription.
        ----------
        """
        if not id_text:
            raise CharterContentException("id_text is not allowed to be empty")
        self.abstract = abstract
        self.abstract_bibls = abstract_bibls
        self.id_norm = id_norm if id_norm else id_text
        self.id_old = id_old
        self.id_text = id_text
        self.transcription_bibls = transcription_bibls

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def abstract(self):
        return self._abstract

    @abstract.setter
    def abstract(self, value: Optional[str | etree._Element] = None):
        if isinstance(value, etree._Element) and (
            ln(value) != "abstract" or ns(value) != CEI_NS
        ):
            raise CharterContentException(
                "Provided value needs to be a string or a 'cei:abstract' element."
            )
        self._abstract = value

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

    def _create_cei_abstract(self) -> Optional[etree._Element]:
        return (
            CEI.abstract(self.abstract)
            if isinstance(self.abstract, str)
            else self.abstract
        )

    def _create_cei_back(self) -> etree._Element:
        return CEI.back()

    def _create_cei_body(self) -> etree._Element:
        children = join(self._create_cei_idno(), self._create_cei_chdesc())
        return CEI.body(*children)

    def _create_cei_chdesc(self) -> Optional[etree._Element]:
        children = join(self._create_cei_abstract())
        return CEI.chDesc(*children) if len(children) else None

    def _create_cei_front(self) -> etree._Element:
        children = join(self._create_cei_source_desc())
        return CEI.front(*children)

    def _create_cei_idno(self) -> etree._Element:
        attributes = {"id": self.id_norm}
        if self.id_old:
            attributes["old"] = self.id_old
        return CEI.idno(self.id_text, **attributes)

    def _create_cei_source_desc(self) -> Optional[etree._Element]:
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
        return CEI.sourceDesc(*children) if len(children) else None

    def _create_cei_text(self) -> etree._Element:
        return CEI.text(
            self._create_cei_front(),
            self._create_cei_body(),
            self._create_cei_back(),
            type="charter",
        )

    # --------------------------------------------------------------------#
    #                          Private methods                           #
    # --------------------------------------------------------------------#

    def _build(self) -> etree._Element:
        return self._create_cei_text()

    # --------------------------------------------------------------------#
    #                           Public methods                           #
    # --------------------------------------------------------------------#

    def to_string(self) -> str:
        return etree.tostring(self._build(), encoding="unicode", pretty_print=True)

    def to_xml(self) -> etree._Element:
        return self._build()
