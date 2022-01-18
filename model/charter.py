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
    _abstract_bibls: List[str] = []
    _archive: Optional[str] = None
    _chancellary_remarks: List[str] = []
    _condition: Optional[str] = None
    _date: Optional[str | etree._Element] = None
    _date_quote: Optional[str | etree._Element] = None
    _date_value: Optional[Time | Tuple[Time, Time]] = None
    _dimensions: Optional[str] = None
    _graphic_urls: List[str] = []
    _id_norm: Optional[str] = None
    _id_old: Optional[str] = None
    _id_text: str = ""
    _issued_place: Optional[str | etree._Element] = None
    _issuer: Optional[str | etree._Element] = None
    _language: Optional[str] = None
    _material: Optional[str] = None
    _notarial_authentication: Optional[str | etree._Element] = None
    _recipient: Optional[str | etree._Element] = None
    _seal_descriptions: Optional[
        etree._Element | str | Seal | List[str] | List[Seal]
    ] = None
    _tradition_form: Optional[str] = None
    _transcription: Optional[str | etree._Element] = None
    _transcription_bibls: List[str] = []

    def __init__(
        self,
        id_text: str,
        abstract: str | etree._Element = None,
        abstract_bibls: str | List[str] = [],
        archive: str = None,
        chancellary_remarks: str | List[str] = [],
        condition: str = None,
        date: str | etree._Element = None,
        date_quote: str | etree._Element = None,
        date_value: DateValue = None,
        dimensions: str = None,
        graphic_urls: str | List[str] = [],
        id_norm: str = None,
        id_old: str = None,
        issued_place: str | etree._Element = None,
        issuer: str | etree._Element = None,
        language: str = None,
        material: str = None,
        notarial_authentication: str | etree._Element = None,
        recipient: str | etree._Element = None,
        seal_descriptions: etree._Element | str | Seal | List[str] | List[Seal] = None,
        tradition_form: str = None,
        transcription: str | etree._Element = None,
        transcription_bibls: str | List[str] = [],
    ) -> None:
        """
        Creates a new charter object.

        Parameters:
        ----------
        id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.

        abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.

        abstract_bibls: The bibliography source or sources for the abstract.

        archive: The name of the archive that owns the original charter.

        chancellary_remarks: Chancellary remarks as a single text or list of texts.

        condition: A description of the charter's condition in text form.

        date: The date the charter was issued at either as text to use when converting to CEI or a complete cei:date or cei:dateRange etree._Element. If the date is given as an XML element, date_value needs to remain emptyself. Missing values will be constructed as having a date of "No date" in the XML.

        date_quote: The charter's date in the original text either as text or a complete cel:quoteOriginaldatierung etree._Element object.

        date_value: The actual date value in case the value in date is just a text and not an XML element. Can bei either an ISO date string, a MOM-compatible string, a python datetime object (can only be between years 1 and 9999) or an astropy Time object - or a tuple with two such values. If a single value is given, it is interpreted as an exact value, otherwise the two values will be used as from/to attributes of a cei:dateRange object. Missing values will be added to the xml as @value="99999999" to conform with the MOM data practices. When a date_value is added and date is an XML element, an exception is raised.

        dimensions: The description of the physical dimensions of the charter as text.

        graphic_urls: A list of strings that represents the urls of various images representing the charter. Can bei either full urls or just the filenames of the image files, depending on the charter fond / collection settings.

        id_norm: A normalized id for the charter. It will be percent-encoded to ensure only valid characters are used. If it is ommitted, the normalized version of id_text will be used.

        id_old: An old, now obsolete identifier of the charter.

        issued_place: The place the charter has been issued at either as text or a complete cei:placeName etree._Element.

        issuer: The issuer of the charter either as text or a complete cei:issuer etree._Element.

        language: The language of the charter as text.

        material: A string description of the material the charter is made of.

        notarial_authentication: A string or complete cei:notariusDesc etree._Element that describes the notarial_authentication of the charter.

        recipient: The recipient of the charter either as text or a complete cei:issuer etree._Element.

        seal_descriptions: The description of the seals of a charter, either as a single/list of simple text descriptions or Seal objects, or a complete cei:sealDesc etree._Element object.

        tradition_form: The form of the charter's tradition, as an original, copy or something else. Can be any free text.

        transcription: The full text transcription of the charter either as text or a complete cei:tenor etree._Element object.

        transcription_bibls: The bibliography source or sources for the transcription.
        ----------
        """
        if not id_text:
            raise CeiException("id_text is not allowed to be empty")
        self.abstract = abstract
        self.abstract_bibls = abstract_bibls
        self.archive = archive
        self.chancellary_remarks = chancellary_remarks
        self.condition = condition
        self.date = date
        self.date_quote = date_quote
        if date_value is not None:
            self.date_value = date_value
        self.dimensions = dimensions
        self.graphic_urls = graphic_urls
        self.id_norm = id_norm
        self.id_old = id_old
        self.id_text = id_text
        self.issued_place = issued_place
        self.issuer = issuer
        self.language = language
        self.material = material
        self.notarial_authentication = notarial_authentication
        self.recipient = recipient
        self.seal_descriptions = seal_descriptions
        self.tradition_form = tradition_form
        self.transcription = transcription
        self.transcription_bibls = transcription_bibls

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
    def abstract_bibls(self):
        return self._abstract_bibls

    @abstract_bibls.setter
    def abstract_bibls(self, value: str | List[str] = []):
        self._abstract_bibls = value if isinstance(value, List) else [value]

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
    def seal_descriptions(self):
        return self._seal_descriptions

    @seal_descriptions.setter
    def seal_descriptions(
        self,
        value: etree._Element | str | Seal | List[str] | List[Seal] = None,
    ):
        validated = (
            validate_element(value, "sealDesc")
            if isinstance(value, etree._Element)
            else value
        )
        if validated is None:
            self._seal_descriptions = None
        else:
            self._seal_descriptions = validated

    @property
    def tradition_form(self):
        return self._tradition_form

    @tradition_form.setter
    def tradition_form(self, value: str = None):
        self._tradition_form = value

    @property
    def transcription(self):
        return self._transcription

    @transcription.setter
    def transcription(self, value: str | etree._Element = None):
        self._transcription = validate_element(value, "tenor")

    @property
    def transcription_bibls(self):
        return self._transcription_bibls

    @transcription_bibls.setter
    def transcription_bibls(self, value: str | List[str] = []):
        self._transcription_bibls = value if isinstance(value, List) else [value]

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

    def _create_cei_arch_identifier(self) -> Optional[etree._Element]:
        return None if not self.archive else CEI.archIdentifier(CEI.arch(self.archive))

    def _create_cei_auth(self) -> Optional[etree._Element]:
        children = join(self._create_cei_notarius_desc(), self._create_cei_seal_desc())
        return CEI.auth(*children) if len(children) else None

    def _create_cei_back(self) -> etree._Element:
        return CEI.back()

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
        children = join(self._create_cei_quote_originaldatierung())
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

    def _create_cei_seal_desc(self) -> Optional[etree._Element]:
        if self.seal_descriptions is None:
            return None
        elif isinstance(self.seal_descriptions, etree._Element):
            return self.seal_descriptions
        elif isinstance(self.seal_descriptions, str):
            return CEI.sealDesc(self.seal_descriptions)
        elif isinstance(self.seal_descriptions, Seal):
            return CEI.sealDesc(self.seal_descriptions.to_xml())
        else:
            # List of strings or Seal objects
            return CEI.sealDesc(
                *[
                    CEI.seal(desc) if isinstance(desc, str) else desc.to_xml()
                    for desc in self.seal_descriptions
                ]
            )

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
        return (
            None if not self._tradition_form else CEI.traditioForm(self._tradition_form)
        )

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
