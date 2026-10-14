import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import urlparse

from lxml import etree

from to_cei._fields import Field, check_fields
from to_cei.config import CEI, CEI_SCHEMA_LOCATION_ATTRIBUTE
from to_cei.dates import NO_DATE_VALUE, DateInput, MomDate, to_mom_date_value
from to_cei.dates import parse as parse_date
from to_cei.helpers import (
    Entries,
    TextOrElement,
    build,
    check_text,
    copy_element,
    get_entries,
    get_str,
    get_str_or_element,
    join,
    required_text,
    runs_together,
    separated,
    text_of,
)
from to_cei.seal import Seal
from to_cei.xml_assembler import XmlAssembler

NO_DATE_TEXT = "Sine dato"
WITNESS_TYPE = "Zeuge"

# Monasterium's rules for charter ids, applied in this order. Its rule for
# ";" checks ":" a second time, so ";" stays, and this copy keeps that.
_MOM_ID_REPLACEMENTS = ((". ", " "), (", ", " "), (" (", "("), (" - ", "-"))
_MOM_ID_TRANSLATION = str.maketrans(
    {
        " ": "_",
        "/": "|",
        "?": None,
        "=": None,
        ":": None,
        "%": None,
        "#": None,
        "$": None,
    }
)

type SealEntry = str | Seal | etree._Element
type SealEntries = SealEntry | Sequence[SealEntry] | None


@dataclass(frozen=True)
class TextWitness:
    """A textual witness of a charter with its form of tradition, written as
    `cei:witness` with `cei:traditioForm`, such as `TextWitness("Kopialbuch
    1, fol. 3", tradition="cop.")`.

    Raises:
        TypeError: if `text` or `tradition` isn't text.
        ValueError: if `text` or `tradition` is empty.
    """

    text: str
    tradition: str | None = None

    def __post_init__(self) -> None:
        check_text(self.text, "text")
        check_text(self.tradition, "tradition", optional=True)


type TextWitnessEntry = str | TextWitness | etree._Element


def mom_id(text: str) -> str:
    """Return `text` cleaned by Monasterium's rules for charter ids.

    ". " and ", " become a space, " (" becomes "(" and " - " becomes "-",
    spaces become "_" and "/" becomes "|", and "?", "=", ":", "%", "#" and
    "$" are removed. An id that ends up empty becomes "0000".
    """
    for old, new in _MOM_ID_REPLACEMENTS:
        text = text.replace(old, new)
    return text.translate(_MOM_ID_TRANSLATION) or "0000"


def _text_or(*tags: str) -> Callable[[TextOrElement], str | etree._Element | None]:
    return lambda value: get_str_or_element(value, *tags)


def _entries(*tags: str) -> Callable[[Entries], list[str | etree._Element]]:
    return lambda value: get_entries(value, *tags)


def _norm_date_value(value: DateInput) -> MomDate | tuple[MomDate, MomDate] | None:
    parsed = parse_date(value)
    days = parsed if isinstance(parsed, tuple) else (parsed,) if parsed else ()
    for day in days:
        to_mom_date_value(day)
    return parsed


def _norm_external_link(value: str | None) -> str | None:
    link = get_str(value)
    if link is None:
        return None
    parsed = urlparse(link)
    if parsed.scheme not in ("http", "https") or "." not in parsed.netloc:
        raise ValueError(
            f"'{link}' does not look like a valid external URL. If you think "
            "it is valid, please contact the to-CEI library maintainers."
        )
    return link


def _norm_witnesses(value: Entries) -> list[str | etree._Element]:
    witnesses = get_entries(value, "persName")
    for witness in witnesses:
        if isinstance(witness, etree._Element) and witness.get("type") not in (
            None,
            WITNESS_TYPE,
        ):
            raise ValueError(
                f"A witness element must have no @type or @type='{WITNESS_TYPE}', "
                f"but has @type='{witness.get('type')}'"
            )
    return witnesses


def _norm_seals(value: SealEntries) -> list[SealEntry]:
    return get_entries(value, "seal", kinds=(Seal,))


def _norm_text_witnesses(
    value: TextWitnessEntry | Sequence[TextWitnessEntry] | None,
) -> list[TextWitnessEntry]:
    return get_entries(value, "witness", kinds=(TextWitness,))


def _build_all(
    entries: Sequence[str | etree._Element], maker: Callable[[str], etree._Element]
) -> list[etree._Element]:
    return [build(entry, maker) for entry in entries]


def _text_witness(entry: TextWitnessEntry) -> etree._Element:
    if isinstance(entry, TextWitness):
        if entry.tradition is None:
            return CEI.witness(entry.text)
        return CEI.witness(*separated(CEI.traditioForm(entry.tradition), entry.text))
    return build(entry, CEI.witness)


def _figure(url: str) -> etree._Element:
    return CEI.figure(CEI.graphic({"url": url}))


class Charter(XmlAssembler):
    abstract: Field[str | etree._Element | None] = Field(_text_or("abstract"))
    abstract_sources: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    archive: Field[str | None] = Field(get_str)
    archive_internal_id: Field[str | None] = Field(get_str)
    archive_location: Field[str | None] = Field(get_str)
    archive_signature: Field[str | None] = Field(get_str)
    chancellary_remarks: Field[list[str | etree._Element]] = Field(_entries("nota"))
    comments: Field[list[str | etree._Element]] = Field(_entries("p"))
    condition: Field[str | etree._Element | None] = Field(_text_or("condition"))
    date: Field[str | etree._Element | None] = Field(_text_or("date", "dateRange"))
    date_quote: Field[str | etree._Element | None] = Field(
        _text_or("quoteOriginaldatierung")
    )
    date_value: Field[MomDate | tuple[MomDate, MomDate] | None] = Field(
        _norm_date_value
    )
    dimensions: Field[str | etree._Element | None] = Field(_text_or("dimensions"))
    external_link: Field[str | None] = Field(_norm_external_link)
    fond: Field[str | None] = Field(get_str)
    footnotes: Field[list[str | etree._Element]] = Field(_entries("note"))
    graphic_urls: Field[list[str | etree._Element]] = Field(_entries("figure"))
    id_old: Field[str | None] = Field(get_str)
    id_text: Field[str] = Field(required_text)
    index: Field[list[str | etree._Element]] = Field(_entries("index"))
    index_geo_features: Field[list[str | etree._Element]] = Field(_entries("geogName"))
    index_organizations: Field[list[str | etree._Element]] = Field(_entries("orgName"))
    index_persons: Field[list[str | etree._Element]] = Field(_entries("persName"))
    index_places: Field[list[str | etree._Element]] = Field(_entries("placeName"))
    issued_place: Field[str | etree._Element | None] = Field(_text_or("placeName"))
    issuers: Field[list[str | etree._Element]] = Field(_entries("issuer"))
    language: Field[str | None] = Field(get_str)
    literature: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    literature_abstracts: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    literature_depictions: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    literature_editions: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    literature_secondary: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    material: Field[str | None] = Field(get_str)
    notarial_authentication: Field[str | etree._Element | None] = Field(
        _text_or("notariusDesc")
    )
    provenance: Field[str | etree._Element | None] = Field(_text_or("provenance"))
    recipient: Field[str | etree._Element | None] = Field(_text_or("recipient"))
    seal_description: Field[str | etree._Element | None] = Field(_text_or("sealDesc"))
    seals: Field[list[SealEntry]] = Field(_norm_seals)
    text_witnesses: Field[list[TextWitnessEntry]] = Field(_norm_text_witnesses)
    tradition: Field[str | None] = Field(get_str)
    transcription: Field[str | etree._Element | None] = Field(_text_or("tenor"))
    transcription_sources: Field[list[str | etree._Element]] = Field(_entries("bibl"))
    witnesses: Field[list[str | etree._Element]] = Field(_norm_witnesses)

    _id_norm: str | None = None

    def __init__(
        self,
        id_text: str,
        *,
        abstract: TextOrElement = None,
        abstract_sources: Entries = None,
        archive: str | None = None,
        archive_internal_id: str | None = None,
        archive_location: str | None = None,
        archive_signature: str | None = None,
        chancellary_remarks: Entries = None,
        comments: Entries = None,
        condition: TextOrElement = None,
        date: TextOrElement = None,
        date_quote: TextOrElement = None,
        date_value: DateInput = None,
        dimensions: TextOrElement = None,
        external_link: str | None = None,
        fond: str | None = None,
        footnotes: Entries = None,
        graphic_urls: Entries = None,
        id_norm: str | None = None,
        id_old: str | None = None,
        index: Entries = None,
        index_geo_features: Entries = None,
        index_organizations: Entries = None,
        index_persons: Entries = None,
        index_places: Entries = None,
        issued_place: TextOrElement = None,
        issuers: Entries = None,
        language: str | None = None,
        literature: Entries = None,
        literature_abstracts: Entries = None,
        literature_depictions: Entries = None,
        literature_editions: Entries = None,
        literature_secondary: Entries = None,
        material: str | None = None,
        notarial_authentication: TextOrElement = None,
        provenance: TextOrElement = None,
        recipient: TextOrElement = None,
        seal_description: TextOrElement = None,
        seals: SealEntries = None,
        text_witnesses: TextWitnessEntry | Sequence[TextWitnessEntry] | None = None,
        tradition: str | None = None,
        transcription: TextOrElement = None,
        transcription_sources: Entries = None,
        witnesses: Entries = None,
    ) -> None:
        """A charter, written as a CEI `cei:text[@type="charter"]`.

        All arguments after `id_text` are keyword-only. They take plain
        values for the common cases. Where CEI allows
        richer content, an argument also accepts the complete CEI element
        it produces, built for example with `to_cei.CEI`. Repeatable
        arguments take one entry or a sequence. Each entry is text or an
        element, and `seals` and `text_witnesses` also take `Seal` and
        `TextWitness` entries. An element must be in the CEI namespace and have the
        expected tag. It's written as a copy, so the caller's element is
        never moved or changed. An element replaces everything to-cei would
        build for it, so arguments that feed into the same element must
        stay empty, which `to_xml` checks. Empty strings count as missing,
        except in `id_text`.

        Args:
            id_text: The charter's identifier, written as `cei:body/cei:idno`.
                Required.
            abstract: The abstract, as text or a `cei:abstract` element. As an
                element, `issuers` and `recipient` must stay empty.
            abstract_sources: Sources of the abstract, as `cei:bibl` entries
                in `cei:sourceDescRegest`.
            archive: The holding archive, as `cei:arch`.
            archive_internal_id: The archive's internal identifier, written
                as `@n` on `cei:archIdentifier/cei:idno`.
            archive_location: The archive's place, as `cei:settlement`.
            archive_signature: The shelf mark in the holding archive, written
                as `cei:archIdentifier/cei:idno`. Defaults to `id_text`.
            chancellary_remarks: Chancellery remarks, as `cei:nota` entries.
            comments: Diplomatic commentary, as `cei:p` entries in
                `cei:diplomaticAnalysis`.
            condition: The physical condition, as text or a `cei:condition`
                element.
            date: The issue date's text, or a complete `cei:date` or
                `cei:dateRange` element. As an element, `date_value` must
                stay empty. Without a text, the text is generated from
                `date_value` (`1457-03-15`, `1457-01-01 – 1457-12-31`), and
                with neither, the date reads "Sine dato" with the value
                `99999999`.
            date_quote: The dating clause as written in the charter, as text
                or a `cei:quoteOriginaldatierung` element.
            date_value: The issue date's value, in any form
                `to_cei.dates.parse` accepts. A single day becomes
                `cei:date[@value]`, a period `cei:dateRange[@from][@to]`. Its
                years must have a MOM value form, as
                `to_cei.dates.to_mom_date_value` describes.
            dimensions: The physical dimensions, as text or a
                `cei:dimensions` element.
            external_link: An http(s) URL of the charter elsewhere, written
                as `cei:archIdentifier/cei:ref/@target`.
            fond: The archival fond, as `cei:archFond`.
            footnotes: Notes, as `cei:note` entries in `cei:back/cei:divNotes`.
            graphic_urls: Images, each as a URL written to
                `cei:figure/cei:graphic/@url` or a complete `cei:figure`
                element. A URL can be complete, a path or a bare filename.
            id_norm: The identifier for `@id` and the file name, in the form
                `mom_id` gives it. Defaults to `id_text`.
            id_old: An earlier shelf mark, as `cei:altIdentifier[@type="old"]`.
            index: Index terms, as `cei:index` entries in `cei:back`.
            index_geo_features: Geographic features, as `cei:geogName`
                entries in `cei:back`.
            index_organizations: Organizations, as `cei:orgName` entries in
                `cei:back`.
            index_persons: Persons, as `cei:persName` entries in `cei:back`.
            index_places: Places, as `cei:placeName` entries in `cei:back`.
            issued_place: The place of issue, as text or a `cei:placeName`
                element.
            issuers: The issuers, as `cei:issuer` entries after the abstract
                text. Following Monasterium's convention, the text
                " Aussteller: " introduces them, and "; " separates them.
            language: The charter's language, as `cei:lang_MOM`.
            literature: Literature, as `cei:bibl` entries in `cei:listBibl`.
            literature_abstracts: Abstracts elsewhere, as `cei:bibl` entries
                in `cei:listBiblRegest`.
            literature_depictions: Depictions, as `cei:bibl` entries in
                `cei:listBiblFaksimile`.
            literature_editions: Editions, as `cei:bibl` entries in
                `cei:listBiblEdition`.
            literature_secondary: Secondary literature, as `cei:bibl`
                entries in `cei:listBiblErw`.
            material: The writing material, as `cei:material`.
            notarial_authentication: The notarial authentication, as text or
                a `cei:notariusDesc` element.
            provenance: The archival provenance, meaning the registry or
                first archive that kept the charter after its active use, as
                text or a `cei:provenance` element in `cei:front`.
            recipient: The recipient, as text or a `cei:recipient` element
                after the issuers, introduced by the text " Empfänger: ".
            seal_description: A general description of the seals, as the
                text of `cei:sealDesc`, or a complete `cei:sealDesc` element.
                As an element, `seals` must stay empty.
            seals: The individual seals, as `cei:seal` entries in
                `cei:sealDesc`. Each is text, a `Seal` or a `cei:seal` element.
            text_witnesses: Textual witnesses of the charter, such as copies
                or inserts, as `cei:witness` entries in `cei:witListPar`. Each
                is a text, a `TextWitness` that also gives the form of
                tradition ("cop.", "ins.") for `cei:traditioForm`, or a
                complete `cei:witness` element.
            tradition: The form of tradition, such as original or copy, as
                `cei:traditioForm`.
            transcription: The full text, as text or a `cei:tenor` element.
            transcription_sources: Sources of the transcription, as
                `cei:bibl` entries in `cei:sourceDescVolltext`.
            witnesses: Witnesses. Following Monasterium's convention, they are
                `cei:persName[@type="Zeuge"]` entries in `cei:back`. A
                `cei:persName` element gets `@type="Zeuge"` on its copy and
                must not have another `@type`. Witnesses within the text are
                marked up with `cei:testis` in an `abstract` or
                `transcription` element.

        Raises:
            TypeError: if a value has the wrong type.
            ValueError: if `id_text` is empty, an element isn't the expected
                CEI element, a witness has another `@type`, `date_value`
                can't be parsed or written as a MOM value, or `external_link`
                isn't an http(s) URL with a dot in its host name.
        """
        self.abstract = abstract
        self.abstract_sources = abstract_sources
        self.archive = archive
        self.archive_internal_id = archive_internal_id
        self.archive_location = archive_location
        self.archive_signature = archive_signature
        self.chancellary_remarks = chancellary_remarks
        self.comments = comments
        self.condition = condition
        self.date = date
        self.date_quote = date_quote
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
        self.provenance = provenance
        self.recipient = recipient
        self.seal_description = seal_description
        self.seals = seals
        self.text_witnesses = text_witnesses
        self.tradition = tradition
        self.transcription = transcription
        self.transcription_sources = transcription_sources
        self.witnesses = witnesses

    @property
    def id_norm(self) -> str:
        """`id_norm`, or else `id_text`, in the form `mom_id` gives it."""
        return mom_id(self._id_norm if self._id_norm else self.id_text)

    @id_norm.setter
    def id_norm(self, value: str | None = None):
        try:
            self._id_norm = get_str(value)
        except TypeError as err:
            raise TypeError(f"id_norm: {err}") from err

    def _create_cei_abstract(self) -> etree._Element | None:
        if isinstance(self.abstract, etree._Element):
            if self.issuers or self.recipient is not None:
                raise ValueError(
                    "Cannot serialize charter: when 'abstract' is an XML element, "
                    "'issuers' and 'recipient' must be empty — please embed those "
                    "markup pieces directly inside the abstract element yourself."
                )
            return copy_element(self.abstract)
        children: list[str | etree._Element] = []
        if self.abstract is not None:
            children.append(self.abstract)

        def label(text: str) -> str:
            before = "".join(text_of(child) for child in children)
            return " " + text if runs_together(before, text) else text

        for position, issuer in enumerate(_build_all(self.issuers, CEI.issuer)):
            children += ["; " if position else label("Aussteller: "), issuer]
        recipient = build(self.recipient, CEI.recipient)
        if recipient is not None:
            children += [label("Empfänger: "), recipient]
        return CEI.abstract(*children) if children else None

    def _create_cei_arch_identifier(self) -> etree._Element | None:
        idno = CEI.idno(self.archive_signature or self.id_text)
        if self.archive_internal_id is not None:
            idno.set("n", self.archive_internal_id)
        parts = separated(
            None
            if self.archive_location is None
            else CEI.settlement(self.archive_location),
            None if self.archive is None else CEI.arch(self.archive),
            None if self.fond is None else CEI.archFond(self.fond),
            idno,
            None
            if self.external_link is None
            else CEI.ref({"target": self.external_link}),
            None
            if self.id_old is None
            else CEI.altIdentifier(self.id_old, {"type": "old"}),
        )
        return CEI.archIdentifier(*parts)

    def _create_cei_auth(self) -> etree._Element | None:
        children = join(
            build(self.notarial_authentication, CEI.notariusDesc),
            self._create_cei_seal_desc(),
        )
        return CEI.auth(*children) if len(children) else None

    def _create_cei_back(self) -> etree._Element:
        witnesses = _build_all(self.witnesses, CEI.persName)
        for witness in witnesses:
            witness.set("type", WITNESS_TYPE)
        notes = _build_all(self.footnotes, CEI.note)
        children = join(
            witnesses,
            _build_all(self.index_persons, CEI.persName),
            _build_all(self.index_organizations, CEI.orgName),
            _build_all(self.index_places, CEI.placeName),
            _build_all(self.index_geo_features, CEI.geogName),
            _build_all(self.index, CEI.index),
            CEI.divNotes(*notes) if len(notes) else None,
        )
        return CEI.back(*children)

    def _create_cei_body(self) -> etree._Element:
        children = join(
            CEI.idno(self.id_text, {"id": self.id_norm}),
            self._create_cei_chdesc(),
            build(self.transcription, CEI.tenor),
        )
        return CEI.body(*children)

    def _create_cei_chdesc(self) -> etree._Element | None:
        witnesses = [_text_witness(entry) for entry in self.text_witnesses]
        children = join(
            self._create_cei_abstract(),
            self._create_cei_issued(),
            self._create_cei_witness_orig(),
            CEI.witListPar(*witnesses) if len(witnesses) else None,
            self._create_cei_diplomatic_analysis(),
            None if self.language is None else CEI.lang_MOM(self.language),
        )
        return CEI.chDesc(*children) if len(children) else None

    def _create_cei_date(self) -> etree._Element:
        if isinstance(self.date, etree._Element):
            if self.date_value is not None:
                raise ValueError(
                    "Cannot serialize charter: when 'date' is an XML element, "
                    "'date_value' must be None — please put the value attributes "
                    "on the date element yourself."
                )
            return copy_element(self.date)
        if isinstance(self.date_value, tuple):
            start, end = self.date_value
            return CEI.dateRange(
                self.date or f"{start.isoformat()} – {end.isoformat()}",
                {"from": to_mom_date_value(start), "to": to_mom_date_value(end)},
            )
        if isinstance(self.date_value, MomDate):
            return CEI.date(
                self.date or self.date_value.isoformat(),
                {"value": to_mom_date_value(self.date_value)},
            )
        return CEI.date(self.date or NO_DATE_TEXT, {"value": NO_DATE_VALUE})

    def _create_cei_diplomatic_analysis(self) -> etree._Element | None:
        children = join(
            self._create_cei_bibls(CEI.listBibl, self.literature),
            self._create_cei_bibls(CEI.listBiblEdition, self.literature_editions),
            self._create_cei_bibls(CEI.listBiblRegest, self.literature_abstracts),
            self._create_cei_bibls(CEI.listBiblFaksimile, self.literature_depictions),
            self._create_cei_bibls(CEI.listBiblErw, self.literature_secondary),
            build(self.date_quote, CEI.quoteOriginaldatierung),
            _build_all(self.comments, CEI.p),
        )
        return CEI.diplomaticAnalysis(*children) if len(children) else None

    def _create_cei_front(self) -> etree._Element:
        children = join(
            self._create_cei_source_desc(), build(self.provenance, CEI.provenance)
        )
        return CEI.front(*children)

    def _create_cei_issued(self) -> etree._Element:
        children = join(
            build(self.issued_place, CEI.placeName), self._create_cei_date()
        )
        return CEI.issued(*children)

    def _create_cei_bibls(
        self,
        maker: Callable[..., etree._Element],
        bibls: Sequence[str | etree._Element],
    ) -> etree._Element | None:
        return maker(*_build_all(bibls, CEI.bibl)) if len(bibls) else None

    def _create_cei_physical_desc(self) -> etree._Element | None:
        children = join(
            None if self.material is None else CEI.material(self.material),
            build(self.dimensions, CEI.dimensions),
            build(self.condition, CEI.condition),
        )
        return CEI.physicalDesc(*children) if len(children) else None

    def _create_cei_seal(self, seal: SealEntry) -> etree._Element | None:
        if isinstance(seal, Seal):
            return seal.to_xml()
        return build(seal, CEI.seal)

    def _create_cei_seal_desc(self) -> etree._Element | None:
        seals = join(*[self._create_cei_seal(seal) for seal in self.seals])
        if isinstance(self.seal_description, etree._Element):
            if seals:
                raise ValueError(
                    "Cannot serialize charter: when 'seal_description' is an XML "
                    "element, 'seals' must be empty — please put the seals inside "
                    "the sealDesc element yourself."
                )
            return copy_element(self.seal_description)
        parts = separated(self.seal_description, *seals)
        return CEI.sealDesc(*parts) if parts else None

    def _create_cei_source_desc(self) -> etree._Element | None:
        children = join(
            self._create_cei_bibls(CEI.sourceDescRegest, self.abstract_sources),
            self._create_cei_bibls(CEI.sourceDescVolltext, self.transcription_sources),
        )
        return CEI.sourceDesc(*children) if len(children) else None

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

    def _create_cei_witness_orig(self) -> etree._Element:
        children = join(
            None if self.tradition is None else CEI.traditioForm(self.tradition),
            self._create_cei_arch_identifier(),
            self._create_cei_auth(),
            self._create_cei_physical_desc(),
            _build_all(self.chancellary_remarks, CEI.nota),
            _build_all(self.graphic_urls, _figure),
        )
        return CEI.witnessOrig(*children)

    def to_xml(self, add_schema_location: bool = False) -> etree._Element:
        """Creates an xml representation of the charter.

        Args:
            add_schema_location: If True, the CEI schema location is added to
                the root element.

        Returns:
            An etree Element object representing the charter.

        Raises:
            TypeError: if a value changed in place, such as an entry appended
                to a list, has the wrong type.
            ValueError: if an element argument conflicts with arguments that
                feed into the same CEI element, or a value changed in place
                isn't the expected CEI element.
        """
        check_fields(self)
        return self._create_cei_text(add_schema_location)

    def to_file(
        self,
        folder: str | os.PathLike[str] | None = None,
        add_schema_location: bool = False,
    ):
        """Writes the charter to `<id_norm>.cei.xml`.

        The name can contain characters that Windows doesn't allow in file names
        (`|`, `*`, `<`, `>`, `"`, `\\`), so writing such a charter fails there.

        Args:
            folder: The folder to write the file to. Defaults to the current
                working directory.
            add_schema_location: If True, the CEI schema location is added to
                the root element.
        """
        self._write_file(
            self.id_norm + ".cei",
            folder=folder,
            add_schema_location=add_schema_location,
        )
