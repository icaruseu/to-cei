import calendar
import re
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import quote

from astropy.time import Time
from lxml import etree

from to_cei.config import CEI, CEI_SCHEMA_LOCATION_ATTRIBUTE
from to_cei.helpers import (get_str, get_str_list, get_str_or_element,
                            get_str_or_element_list, join)
from to_cei.seal import Seal
from to_cei.xml_assembler import XmlAssembler

MOM_DATE_REGEX = re.compile(
    r"^(?P<year>-?[129]?[0-9][0-9][0-9])(?P<month>[019][0-9])(?P<day>[01239][0-9])$"
)
NO_DATE_TEXT = "No date"
NO_DATE_VALUE = "99999999"

SIMPLE_URL_REGEX = re.compile(r"^https?://.{1,}\..{1,}$")

Date = str | datetime | Time

DateValue = Optional[Date | Tuple[Date, Date]]


def to_mom_date_value(time: Time) -> str:
    """Converts an astropy.Time object to a mom-compatible date string.

    Args:
        time (Time): An astropy.Time object

    Returns:
        A date string compatible with mom-ca.
    """
    year = time.ymdhms[0]
    month = time.ymdhms[1]
    day = time.ymdhms[2]
    return "{year}{month}{day}".format(
        year=str(year).zfill(3) if year >= 0 else "-" + str(year * -1).zfill(3),
        month=str(month).zfill(2),
        day=str(day).zfill(2),
    )


def mom_date_to_time(value: str) -> Time | Tuple[Time, Time]:
    """Converts a mom-compatible date string into an astropy.Time object if possible.

    Args:
        value (str): A mom-compatible date string in the form of -?[129]?[0-9][0-9][0-9][019][0-9][01239][0-9]

    Returns:
        A astropy.Time object

    Raises:
        ValueError: If the provided value cannot be converted to a valid astropy.Time object

    """
    match = re.search(MOM_DATE_REGEX, value)
    if match is None:
        raise ValueError("Invalid mom date value provided: '{}'".format(value))
    year = match.group("year")
    if not isinstance(year, str):
        raise ValueError("Invalid year in mom date value: {}".format(year))
    month = match.group("month")
    if not isinstance(month, str):
        raise ValueError("Invalid month in mom date value: {}".format(month))
    day = match.group("day")
    if not isinstance(day, str):
        raise ValueError("Invalid day in mom date value: {}".format(day))
    if month == "99":
        return (
            Time(
                {"year": int(year), "month": 1, "day": 1},
                format="ymdhms",
                scale="ut1",
            ),
            Time(
                {
                    "year": int(year),
                    "month": 12,
                    "day": 31,
                },
                format="ymdhms",
                scale="ut1",
            ),
        )
    if day == "99":
        return (
            Time(
                {"year": int(year), "month": int(month), "day": 1},
                format="ymdhms",
                scale="ut1",
            ),
            Time(
                {
                    "year": int(year),
                    "month": int(month),
                    "day": calendar.monthrange(int(year), int(month))[1],
                },
                format="ymdhms",
                scale="ut1",
            ),
        )
    return Time(
        {"year": int(year), "month": int(month), "day": int(day)},
        format="ymdhms",
        scale="ut1",
    )


def extract_time(time: Time | Tuple[Time, Time]) -> Time:
    """Extract time from date
    Args:
    time (Time | Tuple[Time, Time])

    Returns:
        The first date if a tuple is provided, the date if a date is provided.
    """
    if isinstance(time, Tuple):
        return time[0]
    else:
        return time


def string_to_time(value: str | Tuple[str, str]) -> Time | Tuple[Time, Time]:
    """Converts a single date string or a tuple of date strings to a matching single or tuple astropy.Time object.

    Args:
        value (str | Tuple[str, str]): A single or tuple of date strings. Can be either an iso-compatible or a mom-ca compatible date string.

    Returns:
        A single or tuple astropy.Time objectself.

    Raises:
        ValueError: If the date/s cannot be converted to astropy.Time objects.
    """
    if isinstance(value, Tuple) and len(value) != 2:
        raise ValueError("Invalid date tuple provided: '{}'".format(value))
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
            try:
                return (
                    extract_time(mom_date_to_time(value[0])),
                    extract_time(mom_date_to_time(value[1])),
                )
            except Exception:
                raise ValueError(
                    "Failed to transform mom string to Time: '{}'".format(value)
                )
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
    _footnotes: List[str] = []
    _graphic_urls: List[str] = []
    _id_norm: Optional[str] = None
    _id_old: Optional[str] = None
    _id_text: str = ""
    _index: List[str | etree._Element] = []
    _index_geo_features: List[str | etree._Element] = []
    _index_organizations: List[str | etree._Element] = []
    _index_persons: List[str | etree._Element] = []
    _index_places: List[str | etree._Element] = []
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
    _witnesses: List[str | etree._Element] = []

    def __init__(
        self,
        id_text: str,
        abstract: Optional[str | etree._Element] = None,
        abstract_sources: Optional[str | List[str]] = [],
        archive: Optional[str] = None,
        chancellary_remarks: Optional[str | List[str]] = [],
        comments: Optional[str | List[str]] = [],
        condition: Optional[str] = None,
        date: Optional[str | etree._Element] = None,
        date_quote: Optional[str | etree._Element] = None,
        date_value: Optional[DateValue] = None,
        dimensions: Optional[str] = None,
        external_link: Optional[str] = None,
        footnotes: Optional[str | List[str]] = [],
        graphic_urls: Optional[str | List[str]] = [],
        id_norm: Optional[str] = None,
        id_old: Optional[str] = None,
        index: Optional[List[str | etree._Element]] = [],
        index_geo_features: Optional[List[str | etree._Element]] = [],
        index_organizations: Optional[List[str | etree._Element]] = [],
        index_persons: Optional[List[str | etree._Element]] = [],
        index_places: Optional[List[str | etree._Element]] = [],
        issued_place: Optional[str | etree._Element] = None,
        issuer: Optional[str | etree._Element] = None,
        language: Optional[str] = None,
        literature: Optional[str | List[str]] = [],
        literature_abstracts: Optional[str | List[str]] = [],
        literature_depictions: Optional[str | List[str]] = [],
        literature_editions: Optional[str | List[str]] = [],
        literature_secondary: Optional[str | List[str]] = [],
        material: Optional[str] = None,
        notarial_authentication: Optional[str | etree._Element] = None,
        recipient: Optional[str | etree._Element] = None,
        seals: Optional[etree._Element | str | Seal | List[str] | List[Seal]] = None,
        tradition: Optional[str] = None,
        transcription: Optional[str | etree._Element] = None,
        transcription_sources: Optional[str] | List[str] = [],
        witnesses: Optional[List[str | etree._Element]] = [],
    ) -> None:
        """
        Creates a new charter object. Empty strings in the parameters are treated similar to None values.

        Args:
            id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.
            abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.
            abstract_sources: The bibliography source or sources for the abstract.
            archive: The name of the archive that owns the original charter.
            chancellary_remarks: Chancellary remarks as a single text or list of texts.
            comments: Diplomatic commentary as text or list of texts.
            condition: A description of the charter's condition in text form.
            date: The date the charter was issued at either as text to use when converting to CEI or a complete cei:date or cei:dateRange etree._Element. If the date is given as an XML element, date_value needs to remain empty. Missing values will be constructed as having a date of "No date" in the XML.
            date_quote: The charter's date in the original text either as text or a complete cel:quoteOriginaldatierung etree._Element object.
            date_value: The actual date value in case the value in date is just a text and not an XML element. Can bei either an ISO date string, a MOM-compatible string, a python datetime object (can only be between years 1 and 9999) or an astropy Time object - or a tuple with two such values. If a single value is given, it is interpreted as an exact value, otherwise the two values will be used as from/to attributes of a cei:dateRange object. Missing values will be added to the xml as @value="99999999" to conform with the MOM data practices. When a date_value is added and date is an XML element, an exception is raised. Values with "99" for month or date will be converted to full year or month date ranges. For months "99" any day value after will be ignored and assumed to be unclear. This means, month "99" will always mean the whole given year.
            dimensions: The description of the physical dimensions of the charter as text.
            external_link: A link to an external representation of the charter as text.
            footnotes: Footnotes as text or list of texts.
            graphic_urls: A list of strings that represents the urls of various images representing the charter. Can bei either full urls or just the filenames of the image files, depending on the charter fond / collection settings.
            id_norm: A normalized id for the charter. It will be percent-encoded to ensure only valid characters are used. If it is ommitted, the normalized version of id_text will be used.
            id_old: An old, now obsolete identifier of the charter.
            index: A list of terms as texts or cei:index etree._Element objects to be included in the index.
            index_geo_features: A list of geographical features as texts or cei:geogName etree._Element objects to be included in the index.
            index_organizations: A list of organizations as texts or cei:orgName etree._Element objects to be included in the index.
            index_persons: A list of persons as texts or cei:persName etree._Element objects to be included in the index.
            index_places: A list of places as texts or cei:placeName etree._Element objects to be included in the index.
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
            witnesses: The list of witnesses either as text or complete cei:persName etree._Element objects. A '@type="Zeuge"' attribute will be added for all etree._Element list items.

        Raises:
            ValueError: Raised when various values don't make sense in the context of the charter creation.
        """
        if not id_text:
            raise ValueError("id_text is not allowed to be empty")
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
        self.footnotes = footnotes
        self.graphic_urls = graphic_urls
        self.id_norm = id_norm
        self.id_old = id_old
        self.id_text = id_text
        self.index = index
        self.index_geo_features = index_geo_features
        self.index_organizations = index_organizations
        self.index_persons = index_persons
        self.index_places = index_places
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
        self.witnesses = witnesses

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def abstract(self):
        return self._abstract

    @abstract.setter
    def abstract(self, value: Optional[str | etree._Element] = None):
        if self.issuer is not None and isinstance(self.issuer, etree._Element):
            raise ValueError(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._abstract = get_str_or_element(value, "abstract")

    @property
    def abstract_sources(self):
        return self._abstract_sources

    @abstract_sources.setter
    def abstract_sources(self, value: Optional[str | List[str]] = []):
        self._abstract_sources = get_str_list(value)

    @property
    def archive(self):
        return self._archive

    @archive.setter
    def archive(self, value: Optional[str] = None):
        self._archive = get_str(value)

    @property
    def chancellary_remarks(self):
        return self._chancellary_remarks

    @chancellary_remarks.setter
    def chancellary_remarks(self, value: Optional[str | List[str]] = []):
        self._chancellary_remarks = get_str_list(value)

    @property
    def comments(self):
        return self._comments

    @comments.setter
    def comments(self, value: Optional[str | List[str]] = []):
        self._comments = get_str_list(value)

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value: Optional[str] = None):
        self._condition = get_str(value)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value: Optional[str | etree._Element] = None):
        self._date = get_str_or_element(value, "date", "dateRange")

    @property
    def date_quote(self):
        return self._date_quote

    @date_quote.setter
    def date_quote(self, value: Optional[str | etree._Element] = None):
        self._date_quote = get_str_or_element(value, "quoteOriginaldatierung")

    @property
    def date_value(self):
        return self._date_value

    @date_value.setter
    def date_value(self, value: Optional[DateValue] = None):
        # Don't allow to directly set date values if an XML date element is present
        if isinstance(self.date, etree._Element):
            raise ValueError(
                "Not allowed to set date value directly if the date is already an XML element."
            )
        # Unknown MOM date (99999999)
        elif (
            isinstance(value, str) and (value == NO_DATE_VALUE or not len(value))
        ) or (
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
            raise ValueError("Invalid date value: '{}'".format(value))

    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value: Optional[str] = None):
        self._dimensions = get_str(value)

    @property
    def external_link(self):
        return self._external_link

    @external_link.setter
    def external_link(self, value: Optional[str] = None):
        if not isinstance(value, str) or len(value) == 0:
            return None
        if not re.match(SIMPLE_URL_REGEX, value):
            raise ValueError(
                "'{}' does not look like a valid external URL. If you think it is valid, please contact the to-CEI library maintainers and tell them.".format(
                    value
                )
            )
        self._external_link = value

    @property
    def footnotes(self):
        return self._footnotes

    @footnotes.setter
    def footnotes(self, value: Optional[str | List[str]] = []):
        self._footnotes = get_str_list(value)

    @property
    def graphic_urls(self):
        return self._graphic_urls

    @graphic_urls.setter
    def graphic_urls(self, value: Optional[str | List[str]] = []):
        self._graphic_urls = get_str_list(value)

    @property
    def id_norm(self):
        return quote(self._id_norm if self._id_norm else self.id_text)

    @id_norm.setter
    def id_norm(self, value: Optional[str] = None):
        self._id_norm = get_str(value)

    @property
    def id_old(self):
        return self._id_old

    @id_old.setter
    def id_old(self, value: Optional[str] = None):
        self._id_old = get_str(value)

    @property
    def id_text(self):
        return self._id_text

    @id_text.setter
    def id_text(self, value: str):
        self._id_text = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value: Optional[List[str | etree._Element]] = []):
        self._index = get_str_or_element_list(value, "index")

    @property
    def index_geo_features(self):
        return self._index_geo_features

    @index_geo_features.setter
    def index_geo_features(self, value: Optional[List[str | etree._Element]] = []):
        self._index_geo_features = get_str_or_element_list(value, "geogName")

    @property
    def index_organizations(self):
        return self._index_organizations

    @index_organizations.setter
    def index_organizations(self, value: Optional[List[str | etree._Element]] = []):
        self._index_organizations = get_str_or_element_list(value, "orgName")

    @property
    def index_persons(self):
        return self._index_persons

    @index_persons.setter
    def index_persons(self, value: Optional[List[str | etree._Element]] = []):
        self._index_persons = get_str_or_element_list(value, "persName")

    @property
    def index_places(self):
        return self._index_places

    @index_places.setter
    def index_places(self, value: Optional[List[str | etree._Element]] = []):
        self._index_places = get_str_or_element_list(value, "placeName")

    @property
    def issued_place(self):
        return self._issued_place

    @issued_place.setter
    def issued_place(self, value: Optional[str | etree._Element] = None):
        self._issued_place = get_str_or_element(value, "placeName")

    @property
    def issuer(self):
        return self._issuer

    @issuer.setter
    def issuer(self, value: Optional[str | etree._Element] = None):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise ValueError(
                "XML element content for both issuer and abstract is not allowed, please join the issuer in the XML abstract yourself"
            )
        self._issuer = get_str_or_element(value, "issuer")

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value: Optional[str] = None):
        self._language = get_str(value)

    @property
    def literature(self):
        return self._literature

    @literature.setter
    def literature(self, value: Optional[str | List[str]] = []):
        self._literature = get_str_list(value)

    @property
    def literature_abstracts(self):
        return self._literature_abstracts

    @literature_abstracts.setter
    def literature_abstracts(self, value: Optional[str | List[str]] = []):
        self._literature_abstracts = get_str_list(value)

    @property
    def literature_depictions(self):
        return self._literature_depictions

    @literature_depictions.setter
    def literature_depictions(self, value: Optional[str | List[str]] = []):
        self._literature_depictions = get_str_list(value)

    @property
    def literature_editions(self):
        return self._literature_editions

    @literature_editions.setter
    def literature_editions(self, value: Optional[str | List[str]] = []):
        self._literature_editions = get_str_list(value)

    @property
    def literature_secondary(self):
        return self._literature_secondary

    @literature_secondary.setter
    def literature_secondary(self, value: Optional[str | List[str]] = []):
        self._literature_secondary = get_str_list(value)

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value: Optional[str] = None):
        self._material = get_str(value)

    @property
    def notarial_authentication(self):
        return self._notarial_authentication

    @notarial_authentication.setter
    def notarial_authentication(self, value: Optional[str | etree._Element] = None):
        self._notarial_authentication = get_str_or_element(value, "notariusDesc")

    @property
    def recipient(self):
        return self._recipient

    @recipient.setter
    def recipient(self, value: Optional[str | etree._Element] = None):
        if value is not None and isinstance(self.abstract, etree._Element):
            raise ValueError(
                "XML element content for both recipient and abstract is not allowed, please join the recipient in the XML abstract yourself"
            )
        self._recipient = get_str_or_element(value, "recipient")

    @property
    def seals(self):
        return self._seals

    @seals.setter
    def seals(
        self,
        value: Optional[etree._Element | str | Seal | List[str] | List[Seal]] = None,
    ):
        if value is None or isinstance(value, str) and len(value) == 0:
            return None
        validated = (
            get_str_or_element(value, "sealDesc")
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
    def tradition(self, value: Optional[str] = None):
        self._tradition = get_str(value)

    @property
    def transcription(self):
        return self._transcription

    @transcription.setter
    def transcription(self, value: Optional[str | etree._Element] = None):
        self._transcription = get_str_or_element(value, "tenor")

    @property
    def transcription_sources(self):
        return self._transcription_sources

    @transcription_sources.setter
    def transcription_sources(self, value: Optional[str | List[str]] = []):
        self._transcription_sources = get_str_list(value)

    @property
    def witnesses(self):
        return self._witnesses

    @witnesses.setter
    def witnesses(self, value: Optional[List[str | etree._Element]] = []):
        self._witnesses = get_str_or_element_list(value, "persName")

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
        children = join(
            [self._create_cei_pers_name(person, type="Zeuge") for person in self.witnesses],  # type: ignore
            [self._create_cei_pers_name(person) for person in self.index_persons],  # type: ignore
            [self._create_cei_org_name(organization) for organization in self.index_organizations],  # type: ignore
            [self._create_cei_place_name(place) for place in self.index_places],  # type: ignore
            [self._create_cei_geog_name(geo_feature) for geo_feature in self.index_geo_features],  # type: ignore
            [self._create_cei_index(term) for term in self.index],  # type: ignore
            self._create_cei_div_notes(),
        )
        return CEI.back(*children)

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

    def _create_cei_div_notes(self) -> List[etree._Element]:
        return (
            CEI.divNotes(*[CEI.note(note) for note in self.footnotes])
            if len(self.footnotes)
            else []
        )

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

    def _create_cei_geog_name(
        self, value: Optional[str | etree._Element]
    ) -> Optional[etree._Element]:
        return CEI.geogName(value) if isinstance(value, str) else value

    def _create_cei_index(
        self, value: Optional[str | etree._Element]
    ) -> Optional[etree._Element]:
        return CEI.index(value) if isinstance(value, str) else value

    def _create_cei_org_name(
        self, value: Optional[str | etree._Element]
    ) -> Optional[etree._Element]:
        return CEI.orgName(value) if isinstance(value, str) else value

    def _create_cei_p(self) -> List[etree._Element]:
        return (
            [CEI.p(comment) for comment in self.comments] if len(self.comments) else []
        )

    def _create_cei_pers_name(
        self, value: Optional[str | etree._Element], type: Optional[str] = None
    ) -> Optional[etree._Element]:
        if isinstance(value, str):
            attributes = {}
            if type is not None:
                attributes["type"] = type
            return CEI.persName(value, attributes)
        elif isinstance(value, etree._Element):
            if type is not None:
                value.set("type", type)
            return value
        else:
            return None

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
        return CEI.placeName(value) if isinstance(value, str) else value

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

    def _create_cei_text(self, add_schema_location: bool = False) -> etree._Element:
        text = CEI.text(
            self._create_cei_front(),
            self._create_cei_body(),
            self._create_cei_back(),
            type="charter",
        )
        if add_schema_location:
            text.attrib.update(CEI_SCHEMA_LOCATION_ATTRIBUTE)
        return text

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

    def to_xml(self, add_schema_location: bool = False) -> etree._Element:
        """Creates an xml representation of the charter.

        Args:
            add_schema_location: If True, the CEI schema location is added to the root element.

        Returns:
            An etree Element object representing the charter.
        """
        return self._create_cei_text(add_schema_location)

    def to_file(self, folder: Optional[str] = None, add_schema_location: bool = False):
        """Writes the xml representation of the charter to a file. The filename is generated from the normalized charter id.

        Args:
            folder (str): The folder to write the file to. If this is ommitted, the file is written to the place where the script is executed from.
            add_schema_location (bool): If True, the CEI schema location is added to the root element. Defaults to False.
        """
        return super(Charter, self).to_file(
            self.id_norm + ".cei",
            folder=folder,
            add_schema_location=add_schema_location,
        )
