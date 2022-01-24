import re
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import quote

from astropy.time import Time
from lxml import etree

from config import CEI
from helpers import join, validate_element
from model.cei_exception import CeiException
from model.seal import Seal
from model.XmlAssembler import XmlAssembler

MOM_DATE_REGEX = re.compile(
    r"^(?P<year>-?[129]?[0-9][0-9][0-9])(?P<month>[019][0-9])(?P<day>[01239][0-9])$"
)
NO_DATE_TEXT = "No date"
NO_DATE_VALUE = "99999999"

SIMPLE_URL_REGEX = re.compile(r"^https?://.{1,}\..{1,}$")

Date = str | datetime | Time

DateValue = Optional[Date | Tuple[Date, Date]]


def to_mom_date_value(time: Time) -> str:
    year = time.ymdhms[0]
    month = time.ymdhms[1]
    day = time.ymdhms[2]
    return "{year}{month}{day}".format(
        year=str(year).zfill(3) if year >= 0 else "-" + str(year * -1).zfill(3),
        month=str(month).zfill(2),
        day=str(day).zfill(2),
    )


def mom_date_to_time(value: str) -> Time:
    match = re.search(MOM_DATE_REGEX, value)
    if match is None:
        raise CeiException("Invalid mom date value provided: '{}'".format(value))
    year = match.group("year")
    if not isinstance(year, str):
        raise CeiException("Invalid year in mom date value: {}".format(year))
    month = match.group("month")
    if not isinstance(month, str):
        raise CeiException("Invalid month in mom date value: {}".format(month))
    day = match.group("day")
    if not isinstance(day, str):
        raise CeiException("Invalid day in mom date value: {}".format(day))
    return Time(
        {"year": int(year), "month": int(month), "day": int(day)},
        format="ymdhms",
        scale="ut1",
    )


def string_to_time(value: str | Tuple[str, str]) -> Time | Tuple[Time, Time]:
    if isinstance(value, Tuple) and len(value) != 2:
        raise CeiException("Invalid date tuple provided: '{}'".format(value))
    try:
        # Try to directly convert from an iso date string
        return (
            Time(value, format="isot", scale="ut1")
            if isinstance(value, str)
            else (
                Time(value[0], format="isot", scale="ut1"),
                Time(value[1], format="isot", scale="ut1"),
            )
        )
    # Direct conversion not possible, try to convert mom date strings
    except Exception:
        if isinstance(value, Tuple):
            return (mom_date_to_time(value[0]), mom_date_to_time(value[1]))
        else:
            return mom_date_to_time(value)


class Charter(XmlAssembler):
    _abstract: Optional[str | etree._Element] = None
    _abstract_sources: List[str] = []
    _archive: Optional[str] = None
    _chancellary_remarks: List[str] = []
    _comments: List[str] = []
    _condition: Optional[str] = None
    _date: Optional[str | etree._Element] = None
    _date_quote: Optional[str | etree._Element] = None
    _date_value: Optional[Time | Tuple[Time, Time]] = None
    _dimensions: Optional[str] = None
    _external_link: Optional[str] = None
    _graphic_urls: List[str] = []
    _id_norm: Optional[str] = None
    _id_old: Optional[str] = None
    _id_text: str = ""
    _issued_place: Optional[str | etree._Element] = None
    _issuer: Optional[str | etree._Element] = None
    _language: Optional[str] = None
    _literature: List[str] = []
    _literature_abstracts: List[str] = []
    _literature_depictions: List[str] = []
    _literature_editions: List[str] = []
    _literature_secondary: List[str] = []
    _material: Optional[str] = None
    _notarial_authentication: Optional[str | etree._Element] = None
    _recipient: Optional[str | etree._Element] = None
    _seals: Optional[etree._Element | str | Seal | List[str] | List[Seal]] = None
    _tradition: Optional[str] = None
    _transcription: Optional[str | etree._Element] = None
    _transcription_sources: List[str] = []

    def __init__(
        self,
        id_text: str,
        abstract: str | etree._Element = None,
        abstract_sources: str | List[str] = [],
        archive: str = None,
        chancellary_remarks: str | List[str] = [],
        comments: str | List[str] = [],
        condition: str = None,
        date: str | etree._Element = None,
        date_quote: str | etree._Element = None,
        date_value: DateValue = None,
        dimensions: str = None,
        external_link: str = None,
        graphic_urls: str | List[str] = [],
        id_norm: str = None,
        id_old: str = None,
        issued_place: str | etree._Element = None,
        issuer: str | etree._Element = None,
        language: str = None,
        literature: str | List[str] = [],
        literature_abstracts: str | List[str] = [],
        literature_depictions: str | List[str] = [],
        literature_editions: str | List[str] = [],
        literature_secondary: str | List[str] = [],
        material: str = None,
        notarial_authentication: str | etree._Element = None,
        recipient: str | etree._Element = None,
        seals: etree._Element | str | Seal | List[str] | List[Seal] = None,
        tradition: str = None,
        transcription: str | etree._Element = None,
        transcription_sources: str | List[str] = [],
    ) -> None:
        """
        Creates a new charter object.

        Parameters:
        ----------
        id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.

        abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.

        abstract_sources: The bibliography source or sources for the abstract.

        archive: The name of the archive that owns the original charter.

        chancellary_remarks: Chancellary remarks as a single text or list of texts.

        comments: Diplomatic commentary as text or list of texts.

        condition: A description of the charter's condition in text form.

        date: The date the charter was issued at either as text to use when converting to CEI or a complete cei:date or cei:dateRange etree._Element. If the date is given as an XML element, date_value needs to remain emptyself. Missing values will be constructed as having a date of "No date" in the XML.

        date_quote: The charter's date in the original text either as text or a complete cel:quoteOriginaldatierung etree._Element object.

        date_value: The actual date value in case the value in date is just a text and not an XML element. Can bei either an ISO date string, a MOM-compatible string, a python datetime object (can only be between years 1 and 9999) or an astropy Time object - or a tuple with two such values. If a single value is given, it is interpreted as an exact value, otherwise the two values will be used as from/to attributes of a cei:dateRange object. Missing values will be added to the xml as @value="99999999" to conform with the MOM data practices. When a date_value is added and date is an XML element, an exception is raised.

        dimensions: The description of the physical dimensions of the charter as text.

        external_link: A link to an external representation of the charter as text.

        graphic_urls: A list of strings that represents the urls of various images representing the charter. Can bei either full urls or just the filenames of the image files, depending on the charter fond / collection settings.

        id_norm: A normalized id for the charter. It will be percent-encoded to ensure only valid characters are used. If it is ommitted, the normalized version of id_text will be used.

        id_old: An old, now obsolete identifier of the charter.

        issued_place: The place the charter has been issued at either as text or a complete cei:placeName etree._Element.

        issuer: The issuer of the charter either as text or a complete cei:issuer etree._Element.

        language: The language of the charter as text.

        literature: A single text or list of texts descibing unspecified literature for the charter.

        literature_abstracts: A single text or list of texts descibing abstracts of the charter.

        literature_depictions: A single text or list of texts descibing depictions of the charter.

        literature_editions: A single text or list of texts descibing editions of the charter.

        literature_secondary: A single text or list of texts descibing secondary literature about the charter.

        material: A string description of the material the charter is made of.

        notarial_authentication: A string or complete cei:notariusDesc etree._Element that describes the notarial_authentication of the charter.

        recipient: The recipient of the charter either as text or a complete cei:issuer etree._Element.

        seals: The description of the seals of a charter, either as a single/list of simple text descriptions or Seal objects, or a complete cei:sealDesc etree._Element object.

        tradition: The status of tradition of the charter, as an original, copy or something else. Can be any free text.

        transcription: The full text transcription of the charter either as text or a complete cei:tenor etree._Element object.

        transcription_sources: The source or sources for the transcription.
        ----------
        """
        if not id_text:
            raise CeiException("id_text is not allowed to be empty")
        self.abstract = abstract
        self.abstract_sources = abstract_sources
        self.archive = archive
        self.chancellary_remarks = chancellary_remarks
        self.comments = comments
        self.condition = condition
        self.date = date
        self.date_quote = date_quote
        if date_value is not None:
            self.date_value = date_value
        self.dimensions = dimensions
        self.external_link = external_link
        self.graphic_urls = graphic_urls
        self.id_norm = id_norm
        self.id_old = id_old
        self.id_text = id_text
        self.issued_place = issued_place
        self.issuer = issuer
        self.language = language
        self.literature = literature
        self.literature_abstracts = literature_abstracts
        self.literature_depictions = literature_depictions
        self.literature_editions = literature_editions
        self.literature_secondary = literature_secondary
        self.material = material
        self.notarial_authentication = notarial_authentication
        self.recipient = recipient
        self.seals = seals
        self.tradition = tradition
        self.transcription = transcription
        self.transcription_sources = transcription_sources

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def abstract(self):
        return self._abstract

    @abstract.setter
    def abstract(self, value: str | etree._Element = None):
        if self.issuer is not None and isinstance(self.issuer, etree._Element):
            raise CeiException(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._abstract = validate_element(value, "abstract")

    @property
    def abstract_sources(self):
        return self._abstract_sources

    @abstract_sources.setter
    def abstract_sources(self, value: str | List[str] = []):
        self._abstract_sources = value if isinstance(value, List) else [value]

    @property
    def archive(self):
        return self._archive

    @archive.setter
    def archive(self, value: str = None):
        self._archive = value

    @property
    def chancellary_remarks(self):
        return self._chancellary_remarks

    @chancellary_remarks.setter
    def chancellary_remarks(self, value: str | List[str] = []):
        self._chancellary_remarks = [value] if isinstance(value, str) else value

    @property
    def comments(self):
        return self._comments

    @comments.setter
    def comments(self, value: str | List[str] = []):
        self._comments = [value] if isinstance(value, str) else value

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value: str = None):
        self._condition = value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value: str | etree._Element = None):
        self._date = validate_element(value, "date", "dateRange")

    @property
    def date_quote(self):
        return self._date_quote

    @date_quote.setter
    def date_quote(self, value: str | etree._Element = None):
        self._date_quote = validate_element(value, "quoteOriginaldatierung")

    @property
    def date_value(self):
        return self._date_value

    @date_value.setter
    def date_value(self, value: DateValue = None):
        # Don't allow to directly set date values if an XML date element is present
        if isinstance(self.date, etree._Element):
            raise CeiException(
                "Not allowed to set date value directly if the date is already an XML element."
            )
        # Unknown MOM date (99999999)
        elif (isinstance(value, str) and value == NO_DATE_VALUE) or (
            isinstance(value, Tuple)
            and len(value) == 2
            and value[0] == NO_DATE_VALUE
            and value[1] == NO_DATE_VALUE
        ):
            self._date_value = None
        # Directly set None, Time and [Time, Time] values
        elif (
            value is None
            or isinstance(value, Time)
            or (
                isinstance(value, Tuple)
                and len(value) == 2
                and isinstance(value[0], Time)
                and isinstance(value[1], Time)
            )
        ):
            self._date_value = value  # type: ignore
        # Convert python date objects
        elif isinstance(value, datetime):
            self._date_value = Time(value, scale="ut1")
        # Convert python date tuples
        elif (
            isinstance(value, Tuple)
            and len(value) == 2
            and isinstance(value[0], datetime)
            and isinstance(value[1], datetime)
        ):
            self._date_value = (
                Time(value[0], scale="ut1"),
                Time(value[1], scale="ut1"),
            )
        # Convert strings
        elif isinstance(value, str):
            self._date_value = string_to_time(value)
        # Convert string tuples
        elif (
            isinstance(value, Tuple)
            and len(value) == 2
            and isinstance(value[0], str)
            and isinstance(value[1], str)
        ):
            self._date_value = string_to_time(value)  # type: ignore
        else:
            raise CeiException("Invalid date value: '{}'".format(value))

    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value: str = None):
        self._dimensions = value

    @property
    def external_link(self):
        return self._external_link

    @external_link.setter
    def external_link(self, value: str = None):
        if value and not re.match(SIMPLE_URL_REGEX, value):
            raise CeiException(
                "'{}' does not look like a valid external URL. If you think it is valid, please contact the to-CEI library maintainers and tell them.".format(
                    value
                )
            )
        self._external_link = value

    @property
    def graphic_urls(self):
        return self._graphic_urls

    @graphic_urls.setter
    def graphic_urls(self, value: str | List[str] = []):
        self._graphic_urls = value if isinstance(value, List) else [value]

    @property
    def id_norm(self):
        return quote(self._id_norm if self._id_norm else self.id_text)

    @id_norm.setter
    def id_norm(self, value: str = None):
        self._id_norm = value

    @property
    def id_old(self):
        return self._id_old

    @id_old.setter
    def id_old(self, value: str = None):
        self._id_old = value

    @property
    def id_text(self):
        return self._id_text

    @id_text.setter
    def id_text(self, value: str):
        self._id_text = value

    @property
    def issued_place(self):
        return self._issued_place

    @issued_place.setter
    def issued_place(self, value: str | etree._Element = None):
        self._issued_place = validate_element(value, "placeName")

    @property
    def issuer(self):
        return self._issuer

    @issuer.setter
    def issuer(self, value: str | etree._Element = None):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise CeiException(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._issuer = validate_element(value, "issuer")

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value: str = None):
        self._language = value

    @property
    def literature(self):
        return self._literature

    @literature.setter
    def literature(self, value: str | List[str] = []):
        self._literature = value if isinstance(value, List) else [value]

    @property
    def literature_abstracts(self):
        return self._literature_abstracts

    @literature_abstracts.setter
    def literature_abstracts(self, value: str | List[str] = []):
        self._literature_abstracts = value if isinstance(value, List) else [value]

    @property
    def literature_depictions(self):
        return self._literature_depictions

    @literature_depictions.setter
    def literature_depictions(self, value: str | List[str] = []):
        self._literature_depictions = value if isinstance(value, List) else [value]

    @property
    def literature_editions(self):
        return self._literature_editions

    @literature_editions.setter
    def literature_editions(self, value: str | List[str] = []):
        self._literature_editions = value if isinstance(value, List) else [value]

    @property
    def literature_secondary(self):
        return self._literature_secondary

    @literature_secondary.setter
    def literature_secondary(self, value: str | List[str] = []):
        self._literature_secondary = value if isinstance(value, List) else [value]

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value: str = None):
        self._material = value

    @property
    def notarial_authentication(self):
        return self._notarial_authentication

    @notarial_authentication.setter
    def notarial_authentication(self, value: str | etree._Element = None):
        self._notarial_authentication = validate_element(value, "notariusDesc")

    @property
    def recipient(self):
        return self._recipient

    @recipient.setter
    def recipient(self, value: str | etree._Element = None):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise CeiException(
                "XML element content for both recipient and abstract is not allowed, please join the recipient in the XML abstract yourself"
            )
        self._recipient = validate_element(value, "recipient")

    @property
    def seals(self):
        return self._seals

    @seals.setter
    def seals(
        self,
        value: etree._Element | str | Seal | List[str] | List[Seal] = None,
    ):
        validated = (
            validate_element(value, "sealDesc")
            if isinstance(value, etree._Element)
            else value
        )
        if validated is None:
            self._seals = None
        else:
            self._seals = validated

    @property
    def tradition(self):
        return self._tradition

    @tradition.setter
    def tradition(self, value: str = None):
        self._tradition = value

    @property
    def transcription(self):
        return self._transcription

    @transcription.setter
    def transcription(self, value: str | etree._Element = None):
        self._transcription = validate_element(value, "tenor")

    @property
    def transcription_sources(self):
        return self._transcription_sources

    @transcription_sources.setter
    def transcription_sources(self, value: str | List[str] = []):
        self._transcription_sources = value if isinstance(value, List) else [value]

    # --------------------------------------------------------------------#
    #                        Private CEI creators                        #
    # --------------------------------------------------------------------#

    def _create_cei_abstract(self) -> Optional[etree._Element]:
        children = join(self._create_cei_recipient(), self._create_cei_issuer())
        return (
            CEI.abstract(self.abstract, *children)
            if isinstance(self.abstract, str)
            else self.abstract
        )

    def _create_cei_arch(self) -> Optional[etree._Element]:
        return None if not self.archive else CEI.arch(self.archive)

    def _create_cei_arch_identifier(self) -> Optional[etree._Element]:
        children = join(self._create_cei_arch(), self._create_cei_ref())
        return CEI.archIdentifier(*children) if len(children) else None

    def _create_cei_auth(self) -> Optional[etree._Element]:
        children = join(self._create_cei_notarius_desc(), self._create_cei_seal_desc())
        return CEI.auth(*children) if len(children) else None

    def _create_cei_back(self) -> etree._Element:
        return CEI.back()

    def _create_cei_bibls(self, bibls: List[str]) -> List[etree._Element]:
        return [CEI.bibl(bibl) for bibl in bibls]

    def _create_cei_body(self) -> etree._Element:
        children = join(
            self._create_cei_idno(), self._create_cei_chdesc(), self._create_cei_tenor()
        )
        return CEI.body(*children)

    def _create_cei_chdesc(self) -> Optional[etree._Element]:
        children = join(
            self._create_cei_abstract(),
            self._create_cei_issued(),
            self._create_cei_witness_orig(),
            self._create_cei_diplomatic_analysis(),
            self._create_cei_lang_mom(),
        )
        return CEI.chDesc(*children) if len(children) else None

    def _create_cei_condition(self) -> Optional[etree._Element]:
        return None if self.condition is None else CEI.condition(self.condition)

    def _create_cei_date(self) -> etree._Element:
        # An xml date
        if isinstance(self.date, etree._Element):
            return self.date
        # A date range tuple
        if isinstance(self.date_value, Tuple):
            return CEI.dateRange(
                "{} - {}".format(
                    self.date_value[0].to_value("fits", subfmt="longdate"),
                    self.date_value[1].to_value("fits", subfmt="longdate"),
                )
                if self.date is None
                else self.date,
                {
                    "from": to_mom_date_value(self.date_value[0]),
                    "to": to_mom_date_value(self.date_value[1]),
                },
            )
        # A single date value
        if isinstance(self.date_value, Time):
            return CEI.date(
                self.date_value.to_value("fits", subfmt="longdate")
                if self.date is None
                else self.date,
                {"value": to_mom_date_value(self.date_value)},
            )
        # Only a date text value
        if isinstance(self.date, str):
            return CEI.date(self.date, {"value": NO_DATE_VALUE})
        # Nothing
        return CEI.date(NO_DATE_TEXT, {"value": NO_DATE_VALUE})

    def _create_cei_dimensions(self) -> Optional[etree._Element]:
        return None if self.dimensions is None else CEI.dimensions(self.dimensions)

    def _create_cei_diplomatic_analysis(self) -> Optional[etree._Element]:
        children = join(
            self._create_cei_list_bibl(),
            self._create_cei_list_bibl_edition(),
            self._create_cei_list_bibl_regest(),
            self._create_cei_list_bibl_faksimile(),
            self._create_cei_list_bibl_erw(),
            self._create_cei_quote_originaldatierung(),
            self._create_cei_p(),
        )
        return CEI.diplomaticAnalysis(*children) if len(children) else None

    def _create_cei_figures(self) -> List[etree._Element]:
        return (
            [CEI.figure(CEI.graphic({"url": url})) for url in self.graphic_urls]
            if len(self.graphic_urls)
            else []
        )

    def _create_cei_front(self) -> etree._Element:
        children = join(self._create_cei_source_desc())
        return CEI.front(*children)

    def _create_cei_idno(self) -> etree._Element:
        attributes = {"id": self.id_norm}
        if self.id_old:
            attributes["old"] = self.id_old
        return CEI.idno(self.id_text, **attributes)

    def _create_cei_issued(self) -> Optional[etree._Element]:
        children = join(
            self._create_cei_place_name(self.issued_place), self._create_cei_date()
        )
        return CEI.issued(*children) if len(children) else None

    def _create_cei_issuer(self) -> Optional[etree._Element]:
        return (
            None
            if self.issuer is None
            else (
                CEI.issuer(self.issuer) if isinstance(self.issuer, str) else self.issuer
            )
        )

    def _create_cei_lang_mom(self) -> Optional[etree._Element]:
        return None if self.language is None else CEI.lang_MOM(self.language)

    def _create_cei_list_bibl(self) -> Optional[etree._Element]:
        return (
            CEI.listBibl(*self._create_cei_bibls(self.literature))
            if len(self.literature)
            else None
        )

    def _create_cei_list_bibl_edition(self) -> Optional[etree._Element]:
        return (
            CEI.listBiblEdition(*self._create_cei_bibls(self.literature_editions))
            if len(self.literature_editions)
            else None
        )

    def _create_cei_list_bibl_erw(self) -> Optional[etree._Element]:
        return (
            CEI.listBiblErw(*self._create_cei_bibls(self.literature_secondary))
            if len(self.literature_secondary)
            else None
        )

    def _create_cei_list_bibl_faksimile(self) -> Optional[etree._Element]:
        return (
            CEI.listBiblFaksimile(*self._create_cei_bibls(self.literature_depictions))
            if len(self.literature_depictions)
            else None
        )

    def _create_cei_list_bibl_regest(self) -> Optional[etree._Element]:
        return (
            CEI.listBiblRegest(*self._create_cei_bibls(self.literature_abstracts))
            if len(self.literature_abstracts)
            else None
        )

    def _create_cei_material(self) -> Optional[etree._Element]:
        return None if self.material is None else CEI.material(self.material)

    def _create_cei_nota(self) -> List[etree._Element]:
        return [CEI.nota(nota) for nota in self.chancellary_remarks]

    def _create_cei_notarius_desc(self) -> Optional[etree._Element]:
        return (
            self.notarial_authentication
            if self.notarial_authentication is None
            or isinstance(self.notarial_authentication, etree._Element)
            else CEI.notariusDesc(self.notarial_authentication)
        )

    def _create_cei_p(self) -> List[etree._Element]:
        return (
            [CEI.p(comment) for comment in self.comments] if len(self.comments) else []
        )

    def _create_cei_physical_desc(self) -> Optional[etree._Element]:
        children = join(
            self._create_cei_material(),
            self._create_cei_dimensions(),
            self._create_cei_condition(),
        )
        return CEI.physicalDesc(*children) if len(children) else None

    def _create_cei_place_name(
        self, value: Optional[str | etree._Element]
    ) -> Optional[etree._Element]:
        return (
            None
            if value is None
            else (CEI.placeName(value) if isinstance(value, str) else value)
        )

    def _create_cei_quote_originaldatierung(self) -> Optional[etree._Element]:
        return (
            self.date_quote
            if self.date_quote is None or isinstance(self.date_quote, etree._Element)
            else CEI.quoteOriginaldatierung(self.date_quote)
        )

    def _create_cei_recipient(self) -> Optional[etree._Element]:
        return (
            None
            if self.recipient is None
            else (
                CEI.recipient(self.recipient)
                if isinstance(self.recipient, str)
                else self.recipient
            )
        )

    def _create_cei_ref(self) -> Optional[etree._Element]:
        return (
            None
            if self.external_link is None
            else CEI.ref({"target": self.external_link})
        )

    def _create_cei_seal_desc(self) -> Optional[etree._Element]:
        if self.seals is None:
            return None
        elif isinstance(self.seals, etree._Element):
            return self.seals
        elif isinstance(self.seals, str):
            return CEI.sealDesc(self.seals)
        elif isinstance(self.seals, Seal):
            return CEI.sealDesc(self.seals.to_xml())
        else:
            # List of strings or Seal objects
            return CEI.sealDesc(
                *[
                    CEI.seal(desc) if isinstance(desc, str) else desc.to_xml()
                    for desc in self.seals
                ]
            )

    def _create_cei_source_desc(self) -> Optional[etree._Element]:
        children = []
        if self.abstract_sources:
            children.append(
                CEI.sourceDescRegest(*self._create_cei_bibls(self.abstract_sources))
            )
        if self.transcription_sources:
            children.append(
                CEI.sourceDescVolltext(
                    *self._create_cei_bibls(self.transcription_sources)
                )
            )
        return CEI.sourceDesc(*children) if len(children) else None

    def _create_cei_tenor(self) -> Optional[etree._Element]:
        return (
            self.transcription
            if self.transcription is None
            or isinstance(self.transcription, etree._Element)
            else CEI.tenor(self.transcription)
        )

    def _create_cei_text(self) -> etree._Element:
        return CEI.text(
            self._create_cei_front(),
            self._create_cei_body(),
            self._create_cei_back(),
            type="charter",
        )

    def _create_cei_traditio_form(self) -> Optional[etree._Element]:
        return None if not self._tradition else CEI.traditioForm(self._tradition)

    def _create_cei_witness_orig(self) -> Optional[etree._Element]:
        children = join(
            self._create_cei_traditio_form(),
            self._create_cei_arch_identifier(),
            self._create_cei_auth(),
            self._create_cei_physical_desc(),
            self._create_cei_nota(),
            self._create_cei_figures(),
        )
        return CEI.witnessOrig(*children) if len(children) else None

    # --------------------------------------------------------------------#
    #                           Public methods                           #
    # --------------------------------------------------------------------#

    def to_xml(self) -> etree._Element:
        return self._create_cei_text()
