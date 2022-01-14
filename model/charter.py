import re
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import quote

from astropy.time import Time
from lxml import etree
from lxml.builder import ElementMaker  # type: ignore


class CharterContentException(Exception):
    pass


CEI_NS: str = "http://www.monasterium.net/NS/cei"
CEI = ElementMaker(namespace=CEI_NS, nsmap={None: CEI_NS})
CHARTER_NSS = {"cei": CEI_NS}

MOM_DATE_REGEX = re.compile(
    r"^(?P<year>-?[129]?[0-9][0-9][0-9])(?P<month>[019][0-9])(?P<day>[01239][0-9])$"
)

NO_DATE_TEXT = "No date"
NO_DATE_VALUE = "99999999"

Date = str | datetime | Time

DateValue = Optional[Date | Tuple[Date, Date]]

StrOrElement = Optional[str | etree._Element]


def join(*values: Optional[etree._Element]):
    """Joins all non-empty values in a list."""
    return [value for value in values if isinstance(value, etree._Element)]


def ln(element: etree._Element) -> str:
    """Get the local name of an element."""
    return etree.QName(element.tag).localname


def ns(element: etree._Element) -> str:
    """Get the namespace of an element."""
    return etree.QName(element.tag).namespace


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
        raise CharterContentException(
            "Invalid mom date value provided: '{}'".format(value)
        )
    year = match.group("year")
    if not isinstance(year, str):
        raise CharterContentException("Invalid year in mom date value: {}".format(year))
    month = match.group("month")
    if not isinstance(month, str):
        raise CharterContentException(
            "Invalid month in mom date value: {}".format(month)
        )
    day = match.group("day")
    if not isinstance(day, str):
        raise CharterContentException("Invalid day in mom date value: {}".format(day))
    return Time(
        {"year": int(year), "month": int(month), "day": int(day)},
        format="ymdhms",
        scale="ut1",
    )


def string_to_time(value: str | Tuple[str, str]) -> Time | Tuple[Time, Time]:
    if isinstance(value, Tuple) and len(value) != 2:
        raise CharterContentException("Invalid date tuple provided: '{}'".format(value))
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


def validate_element(value: StrOrElement, *tags: str) -> StrOrElement:
    if isinstance(value, etree._Element):
        if ns(value) != CEI_NS:
            raise CharterContentException(
                "Provided element needs to be in the CEI namespace but instead is in '{}'".format(
                    ns(value)
                )
            )
        if ln(value) not in tags:
            raise CharterContentException(
                "Provided element needs to be one of '{}', but instead is '{}'".format(
                    ", ".join(tags), ln(value)
                )
            )
    return value


class Charter:
    _abstract: StrOrElement = None
    _abstract_bibls: List[str] = []
    _date: StrOrElement = None
    _date_value: Optional[Time | Tuple[Time, Time]] = None
    _id_norm: str = ""
    _id_old: Optional[str] = None
    _id_text: str = ""
    _issued_place: StrOrElement = None
    _issuer: StrOrElement = None
    _recipient: StrOrElement = None
    _transcription_bibls: List[str] = []

    def __init__(
        self,
        id_text: str,
        abstract: StrOrElement = None,
        abstract_bibls: str | List[str] = [],
        date: StrOrElement = None,
        date_value: DateValue = None,
        id_norm: Optional[str] = None,
        id_old: Optional[str] = None,
        issued_place: StrOrElement = None,
        issuer: StrOrElement = None,
        recipient: StrOrElement = None,
        transcription_bibls: str | List[str] = [],
    ) -> None:
        """
        Creates a new charter object.

        Parameters:
        ----------
        id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.

        abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.

        abstract_bibls: The bibliography source or sources for the abstract.

        date: The date the charter was issued at either as text to use when converting to CEI or a complete cei:date or cei:dateRange etree._Element. If the date is given as an XML element, date_value needs to remain emptyself. Missing values will be constructed as having a date of "No date" in the XML.

        date_value: The actual date value in case the value in date is just a text and not an XML element. Can bei either an ISO date string, a MOM-compatible string, a python datetime object (can only be between years 1 and 9999) or an astropy Time object - or a tuple with two such values. If a single value is given, it is interpreted as an exact value, otherwise the two values will be used as from/to attributes of a cei:dateRange object. Missing values will be added to the xml as @value="99999999" to conform with the MOM data practices. When a date_value is added and date is an XML element, an exception is raised.

        id_norm: A normalized id for the charter. It will be percent-encoded to ensure only valid characters are used. If it is ommitted, the normalized version of id_text will be used.

        id_old: An old, now obsolete identifier of the charter.

        issued_place: The place the charter has been issued at either as text or a complete cei:placeName etree._Element.

        issuer: The issuer of the charter either as text or a complete cei:issuer etree._Element.

        recipient: The recipient of the charter either as text or a complete cei:issuer etree._Element.

        transcription_bibls: The bibliography source or sources for the transcription.
        ----------
        """
        if not id_text:
            raise CharterContentException("id_text is not allowed to be empty")
        self.abstract = abstract
        self.abstract_bibls = abstract_bibls
        self.date = date
        if date_value is not None:
            self.date_value = date_value
        self.id_norm = id_norm if id_norm else id_text
        self.id_old = id_old
        self.id_text = id_text
        self.issued_place = issued_place
        self.issuer = issuer
        self.recipient = recipient
        self.transcription_bibls = transcription_bibls

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def abstract(self):
        return self._abstract

    @abstract.setter
    def abstract(self, value: StrOrElement = None):
        if self.issuer is not None and isinstance(self.issuer, etree._Element):
            raise CharterContentException(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._abstract = validate_element(value, "abstract")

    @property
    def abstract_bibls(self):
        return self._abstract_bibls

    @abstract_bibls.setter
    def abstract_bibls(self, value: str | List[str]):
        self._abstract_bibls = value if isinstance(value, List) else [value]

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value: StrOrElement):
        self._date = validate_element(value, "date", "dateRange")

    @property
    def date_value(self):
        return self._date_value

    @date_value.setter
    def date_value(self, value: DateValue):
        # Don't allow to directly set date values if an XML date element is present
        if isinstance(self.date, etree._Element):
            raise CharterContentException(
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
            raise CharterContentException("Invalid date value: '{}'".format(value))

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
    def issued_place(self):
        return self._issued_place

    @issued_place.setter
    def issued_place(self, value: StrOrElement):
        self._issued_place = validate_element(value, "placeName")

    @property
    def issuer(self):
        return self._issuer

    @issuer.setter
    def issuer(self, value: StrOrElement):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise CharterContentException(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._issuer = validate_element(value, "issuer")

    @property
    def recipient(self):
        return self._recipient

    @recipient.setter
    def recipient(self, value: StrOrElement):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise CharterContentException(
                "XML element content for both recipient and abstract is not allowed, please join the recipient in the XML abstract yourself"
            )
        self._recipient = validate_element(value, "recipient")

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
        children = join(self._create_cei_recipient(), self._create_cei_issuer())
        return (
            CEI.abstract(self.abstract, *children)
            if isinstance(self.abstract, str)
            else self.abstract
        )

    def _create_cei_back(self) -> etree._Element:
        return CEI.back()

    def _create_cei_body(self) -> etree._Element:
        children = join(self._create_cei_idno(), self._create_cei_chdesc())
        return CEI.body(*children)

    def _create_cei_chdesc(self) -> Optional[etree._Element]:
        children = join(self._create_cei_abstract(), self._create_cei_issued())
        return CEI.chDesc(*children) if len(children) else None

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

    def _create_cei_place_name(self, value: StrOrElement) -> Optional[etree._Element]:
        return (
            None
            if value is None
            else (CEI.placeName(value) if isinstance(value, str) else value)
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
