from datetime import datetime
from urllib.parse import quote, urlparse

from astropy.time import Time
from lxml import etree

from to_cei._fields import CharterField
from to_cei.config import CEI, CEI_SCHEMA_LOCATION_ATTRIBUTE
from to_cei.dates import (NO_DATE_VALUE, parse as parse_date,
                          to_mom_date_value)
from to_cei.helpers import (get_str, get_str_list, get_str_or_element,
                            get_str_or_element_list, join)
from to_cei.seal import Seal
from to_cei.xml_assembler import XmlAssembler

NO_DATE_TEXT = "No date"

Date = str | datetime | Time

DateValue = Date | tuple[Date, Date] | None


# Field normalizer factories used by the CharterField declarations.
def _norm_str_or_element(*tags: str):
    return lambda value: get_str_or_element(value, *tags)


def _norm_str_or_element_list(*tags: str):
    return lambda value: get_str_or_element_list(value, *tags)


def _norm_id_text(value):
    return value if isinstance(value, str) else ""


class Charter(XmlAssembler):
    # Declarative fields. Bespoke ones (id_norm, date_value, external_link,
    # issuers, seals) keep hand-written properties below.
    abstract = CharterField(_norm_str_or_element("abstract"))
    abstract_sources = CharterField(get_str_list)
    archive = CharterField(get_str)
    archive_location = CharterField(get_str)
    chancellary_remarks = CharterField(get_str_list)
    comments = CharterField(get_str_list)
    condition = CharterField(get_str)
    date = CharterField(_norm_str_or_element("date", "dateRange"))
    date_quote = CharterField(_norm_str_or_element("quoteOriginaldatierung"))
    dimensions = CharterField(get_str)
    fond = CharterField(get_str)
    footnotes = CharterField(get_str_list)
    graphic_urls = CharterField(get_str_list)
    id_old = CharterField(get_str)
    id_text = CharterField(_norm_id_text)
    index = CharterField(_norm_str_or_element_list("index"))
    index_geo_features = CharterField(_norm_str_or_element_list("geogName"))
    index_organizations = CharterField(_norm_str_or_element_list("orgName"))
    index_persons = CharterField(_norm_str_or_element_list("persName"))
    index_places = CharterField(_norm_str_or_element_list("placeName"))
    issued_place = CharterField(_norm_str_or_element("placeName"))
    language = CharterField(get_str)
    literature = CharterField(get_str_list)
    literature_abstracts = CharterField(get_str_list)
    literature_depictions = CharterField(get_str_list)
    literature_editions = CharterField(get_str_list)
    literature_secondary = CharterField(get_str_list)
    material = CharterField(get_str)
    notarial_authentication = CharterField(_norm_str_or_element("notariusDesc"))
    recipient = CharterField(_norm_str_or_element("recipient"))
    tradition = CharterField(get_str)
    transcription = CharterField(_norm_str_or_element("tenor"))
    transcription_sources = CharterField(get_str_list)
    witnesses = CharterField(_norm_str_or_element_list("persName"))

    # Defaults for bespoke hand-written properties (see below).
    _id_norm: str | None = None
    _date_value: Time | tuple[Time, Time] | None = None
    _external_link: str | None = None
    _issuers: str | etree._Element | list[str] | list[etree._Element] | None = None
    _seals: etree._Element | str | Seal | list[str] | list[Seal] | None = None

    def __init__(
        self,
        id_text: str,
        abstract: str | etree._Element | None = None,
        abstract_sources: str | list[str] | None = None,
        archive: str | None = None,
        archive_location: str | None = None,
        chancellary_remarks: str | list[str] | None = None,
        comments: str | list[str] | None = None,
        condition: str | None = None,
        date: str | etree._Element | None = None,
        date_quote: str | etree._Element | None = None,
        date_value: DateValue | None = None,
        dimensions: str | None = None,
        external_link: str | None = None,
        fond: str | None = None,
        footnotes: str | list[str] | None = None,
        graphic_urls: str | list[str] | None = None,
        id_norm: str | None = None,
        id_old: str | None = None,
        index: list[str | etree._Element] | None = None,
        index_geo_features: list[str | etree._Element] | None = None,
        index_organizations: list[str | etree._Element] | None = None,
        index_persons: list[str | etree._Element] | None = None,
        index_places: list[str | etree._Element] | None = None,
        issued_place: str | etree._Element | None = None,
        issuers: None | (
            str | etree._Element | list[str] | list[etree._Element]
        ) = None,
        language: str | None = None,
        literature: str | list[str] | None = None,
        literature_abstracts: str | list[str] | None = None,
        literature_depictions: str | list[str] | None = None,
        literature_editions: str | list[str] | None = None,
        literature_secondary: str | list[str] | None = None,
        material: str | None = None,
        notarial_authentication: str | etree._Element | None = None,
        recipient: str | etree._Element | None = None,
        seals: etree._Element | str | Seal | list[str] | list[Seal] | None = None,
        tradition: str | None = None,
        transcription: str | etree._Element | None = None,
        transcription_sources: str | None | list[str] = None,
        witnesses: list[str | etree._Element] | None = None,
    ) -> None:
        """
        Creates a new charter object. Empty strings in the parameters are treated similar to None values.

        Args:
            id_text: The human readable id of the charter. If id_norm is not present, id_text will be used in a normalized form. If it is missing or empty, an exception will be raised.
            abstract: The abstract either as a simple text or a complete cei:abstract etree._Element.
            abstract_sources: The bibliography source or sources for the abstract.
            archive: The name of the archive that owns the original charter.
            archive_location: The city or other location of the archive that owns the original charter.
            chancellary_remarks: Chancellary remarks as a single text or list of texts.
            comments: Diplomatic commentary as text or list of texts.
            condition: A description of the charter's condition in text form.
            date: The date the charter was issued at either as text to use when converting to CEI or a complete cei:date or cei:dateRange etree._Element. If the date is given as an XML element, date_value needs to remain empty. Missing values will be constructed as having a date of "No date" in the XML.
            date_quote: The charter's date in the original text either as text or a complete cel:quoteOriginaldatierung etree._Element object.
            date_value: The actual date value in case the value in date is just a text and not an XML element. Can bei either an ISO date string, a MOM-compatible string, a python datetime object (can only be between years 1 and 9999) or an astropy Time object - or a tuple with two such values. If a single value is given, it is interpreted as an exact value, otherwise the two values will be used as from/to attributes of a cei:dateRange object. Missing values will be added to the xml as @value="99999999" to conform with the MOM data practices. When a date_value is added and date is an XML element, an exception is raised. Values with "99" for month or date will be converted to full year or month date ranges. For months "99" any day value after will be ignored and assumed to be unclear. This means, month "99" will always mean the whole given year.
            dimensions: The description of the physical dimensions of the charter as text.
            external_link: A link to an external representation of the charter as text.
            fond: The archival fond the charter is part of.
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
            issuers: The charters' issuers, as either a single or list of texts or complete cei:issuer etree._Element objects.
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
        self.archive_location = archive_location
        self.chancellary_remarks = chancellary_remarks
        self.comments = comments
        self.condition = condition
        self.date = date
        self.date_quote = date_quote
        if date_value is not None:
            self.date_value = date_value
        self.dimensions = dimensions
        self.external_link = external_link
        self.fond = fond
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
        self.issuers = issuers
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
    #                       Bespoke field properties                     #
    # --------------------------------------------------------------------#
    # Fields with logic that doesn't fit a single normalization callable.

    @property
    def id_norm(self):
        """Percent-encoded id; falls back to a normalized `id_text`."""
        return quote(self._id_norm if self._id_norm else self.id_text)

    @id_norm.setter
    def id_norm(self, value: str | None = None):
        self._id_norm = get_str(value)

    @property
    def date_value(self):
        return self._date_value

    @date_value.setter
    def date_value(self, value: DateValue | None = None):
        if isinstance(self.date, etree._Element):
            raise ValueError(
                "Cannot set date_value when 'date' is already an XML element."
            )
        # Shape and no-date handling live in to_cei.dates.parse.
        self._date_value = parse_date(value)  # type: ignore[arg-type]

    @property
    def external_link(self):
        return self._external_link

    @external_link.setter
    def external_link(self, value: str | None = None):
        if not isinstance(value, str) or len(value) == 0:
            self._external_link = None
            return
        parsed = urlparse(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.netloc
            or "." not in parsed.netloc
        ):
            raise ValueError(
                f"'{value}' does not look like a valid external URL. If you think "
                "it is valid, please contact the to-CEI library maintainers."
            )
        self._external_link = value

    @property
    def issuers(self):
        return self._issuers

    @issuers.setter
    def issuers(
        self,
        value: str | etree._Element | list[str] | list[etree._Element] | None = None,
    ):
        # Mutual exclusion with an XML `abstract` is enforced at
        # serialization in `_create_cei_abstract`, not here.
        if value is None:
            self._issuers = None
            return
        if isinstance(value, etree._Element):
            get_str_or_element(value, "issuer")
        elif isinstance(value, list):
            for item in value:
                get_str_or_element(item, "issuer")
        self._issuers = value

    @property
    def seals(self):
        return self._seals

    @seals.setter
    def seals(
        self,
        value: etree._Element | str | Seal | list[str] | list[Seal] | None = None,
    ):
        if value is None or (isinstance(value, str) and len(value) == 0):
            self._seals = None
            return
        if isinstance(value, etree._Element):
            self._seals = get_str_or_element(value, "sealDesc")
        else:
            self._seals = value

    # --------------------------------------------------------------------#
    #                        Private CEI creators                        #
    # --------------------------------------------------------------------#

    def _create_cei_abstract(self) -> etree._Element | None:
        if isinstance(self.abstract, etree._Element) and (
            self.issuers is not None or self.recipient is not None
        ):
            raise ValueError(
                "Cannot serialize charter: when 'abstract' is an XML element, "
                "'issuers' and 'recipient' must be None — please embed those "
                "markup pieces directly inside the abstract element yourself."
            )
        children = join(self._create_cei_recipient(), *self._create_cei_issuers())
        return (
            CEI.abstract(self.abstract, *children)
            if isinstance(self.abstract, str)
            else self.abstract
        )

    def _create_cei_arch(self) -> etree._Element | None:
        return None if not self.archive else CEI.arch(self.archive)
    
    def _create_cei_arch_fond(self) -> etree._Element | None:
        return None if not self.fond else CEI.archFond(self.fond)
    
    def _create_cei_settlement(self) -> etree._Element | None:
        return None if not self.archive_location else CEI.settlement(self.archive_location)
    
    def _create_cei_arch_identifier(self) -> etree._Element | None:
        children = join(
            self._create_cei_settlement(),
            self._create_cei_arch(),
            self._create_cei_arch_fond(),
            self._create_cei_idno(),
            self._create_cei_ref(),
            self._create_cei_alt_identifier(),
        )
        return CEI.archIdentifier(*children) if len(children) else None

    def _create_cei_alt_identifier(self) -> etree._Element | None:
        return (
            None if not self.id_old else CEI.altIdentifier(self.id_old, {"type": "old"})
        )

    def _create_cei_auth(self) -> etree._Element | None:
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

    def _create_cei_bibls(self, bibls: list[str]) -> list[etree._Element]:
        return [CEI.bibl(bibl) for bibl in bibls]

    def _create_cei_body(self) -> etree._Element:
        children = join(
            self._create_cei_idno(), self._create_cei_chdesc(), self._create_cei_tenor()
        )
        return CEI.body(*children)

    def _create_cei_chdesc(self) -> etree._Element | None:
        children = join(
            self._create_cei_abstract(),
            self._create_cei_issued(),
            self._create_cei_witness_orig(),
            self._create_cei_diplomatic_analysis(),
            self._create_cei_lang_mom(),
        )
        return CEI.chDesc(*children) if len(children) else None

    def _create_cei_condition(self) -> etree._Element | None:
        return None if self.condition is None else CEI.condition(self.condition)

    def _create_cei_date(self) -> etree._Element:
        # An xml date
        if isinstance(self.date, etree._Element):
            return self.date
        # A date range tuple
        if isinstance(self.date_value, tuple):
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

    def _create_cei_dimensions(self) -> etree._Element | None:
        return None if self.dimensions is None else CEI.dimensions(self.dimensions)

    def _create_cei_diplomatic_analysis(self) -> etree._Element | None:
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

    def _create_cei_div_notes(self) -> list[etree._Element]:
        return (
            CEI.divNotes(*[CEI.note(note) for note in self.footnotes])
            if len(self.footnotes)
            else []
        )

    def _create_cei_figures(self) -> list[etree._Element]:
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
        return CEI.idno(self.id_text, **attributes)

    def _create_cei_issued(self) -> etree._Element | None:
        children = join(
            self._create_cei_place_name(self.issued_place), self._create_cei_date()
        )
        return CEI.issued(*children) if len(children) else None

    def _create_cei_issuers(self) -> list[etree._Element]:
        if self.issuers is None:
            return []
        elif isinstance(self.issuers, str):
            return [CEI.issuer(self.issuers)]
        elif isinstance(self.issuers, list):
            return [
                CEI.issuer(issuer) if isinstance(issuer, str) else issuer
                for issuer in self.issuers
            ]
        else:
            return [self.issuers]

    def _create_cei_lang_mom(self) -> etree._Element | None:
        return None if self.language is None else CEI.lang_MOM(self.language)

    def _create_cei_list_bibl(self) -> etree._Element | None:
        return (
            CEI.listBibl(*self._create_cei_bibls(self.literature))
            if len(self.literature)
            else None
        )

    def _create_cei_list_bibl_edition(self) -> etree._Element | None:
        return (
            CEI.listBiblEdition(*self._create_cei_bibls(self.literature_editions))
            if len(self.literature_editions)
            else None
        )

    def _create_cei_list_bibl_erw(self) -> etree._Element | None:
        return (
            CEI.listBiblErw(*self._create_cei_bibls(self.literature_secondary))
            if len(self.literature_secondary)
            else None
        )

    def _create_cei_list_bibl_faksimile(self) -> etree._Element | None:
        return (
            CEI.listBiblFaksimile(*self._create_cei_bibls(self.literature_depictions))
            if len(self.literature_depictions)
            else None
        )

    def _create_cei_list_bibl_regest(self) -> etree._Element | None:
        return (
            CEI.listBiblRegest(*self._create_cei_bibls(self.literature_abstracts))
            if len(self.literature_abstracts)
            else None
        )

    def _create_cei_material(self) -> etree._Element | None:
        return None if self.material is None else CEI.material(self.material)

    def _create_cei_nota(self) -> list[etree._Element]:
        return [CEI.nota(nota) for nota in self.chancellary_remarks]

    def _create_cei_notarius_desc(self) -> etree._Element | None:
        return (
            self.notarial_authentication
            if self.notarial_authentication is None
            or isinstance(self.notarial_authentication, etree._Element)
            else CEI.notariusDesc(self.notarial_authentication)
        )

    def _create_cei_geog_name(
        self, value: str | etree._Element | None
    ) -> etree._Element | None:
        return CEI.geogName(value) if isinstance(value, str) else value

    def _create_cei_index(
        self, value: str | etree._Element | None
    ) -> etree._Element | None:
        return CEI.index(value) if isinstance(value, str) else value

    def _create_cei_org_name(
        self, value: str | etree._Element | None
    ) -> etree._Element | None:
        return CEI.orgName(value) if isinstance(value, str) else value

    def _create_cei_p(self) -> list[etree._Element]:
        return (
            [CEI.p(comment) for comment in self.comments] if len(self.comments) else []
        )

    def _create_cei_pers_name(
        self, value: str | etree._Element | None, type: str | None = None
    ) -> etree._Element | None:
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

    def _create_cei_physical_desc(self) -> etree._Element | None:
        children = join(
            self._create_cei_material(),
            self._create_cei_dimensions(),
            self._create_cei_condition(),
        )
        return CEI.physicalDesc(*children) if len(children) else None

    def _create_cei_place_name(
        self, value: str | etree._Element | None
    ) -> etree._Element | None:
        return CEI.placeName(value) if isinstance(value, str) else value

    def _create_cei_quote_originaldatierung(self) -> etree._Element | None:
        return (
            self.date_quote
            if self.date_quote is None or isinstance(self.date_quote, etree._Element)
            else CEI.quoteOriginaldatierung(self.date_quote)
        )

    def _create_cei_recipient(self) -> etree._Element | None:
        return (
            None
            if self.recipient is None
            else (
                CEI.recipient(self.recipient)
                if isinstance(self.recipient, str)
                else self.recipient
            )
        )

    def _create_cei_ref(self) -> etree._Element | None:
        return (
            None
            if self.external_link is None
            else CEI.ref({"target": self.external_link})
        )

    def _create_cei_seal_desc(self) -> etree._Element | None:
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

    def _create_cei_source_desc(self) -> etree._Element | None:
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

    def _create_cei_tenor(self) -> etree._Element | None:
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

    def _create_cei_traditio_form(self) -> etree._Element | None:
        return None if not self._tradition else CEI.traditioForm(self._tradition)

    def _create_cei_witness_orig(self) -> etree._Element | None:
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

    def to_file(self, folder: str | None = None, add_schema_location: bool = False):
        """Writes the xml representation of the charter to a file. The filename is generated from the normalized charter id.

        Args:
            folder (str): The folder to write the file to. If this is ommitted, the file is written to the place where the script is executed from.
            add_schema_location (bool): If True, the CEI schema location is added to the root element. Defaults to False.
        """
        return super().to_file(
            self.id_norm + ".cei",
            folder=folder,
            add_schema_location=add_schema_location,
        )
