import pathlib
from datetime import datetime

import pytest
from lxml import etree

from pytest_helpers import xp, xps
from to_cei.charter import NO_DATE_VALUE, Charter, TextWitness, mom_id
from to_cei.config import CEI, CHARTER_NSS, SCHEMA_LOCATION, SCHEMA_LOCATION_QNAME
from to_cei.dates import MomDate
from to_cei.helpers import ln
from to_cei.seal import Seal
from to_cei.validator import Validator


def test_has_correct_base_structure():
    direct_children = xp(Charter(id_text="1"), "/cei:text/child::*")
    assert len(direct_children) == 3
    assert ln(direct_children[0]) == "front"
    assert ln(direct_children[1]) == "body"
    assert ln(direct_children[2]) == "back"


def test_is_valid_charter():
    charter = Charter(
        "1307 II 22",
        abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
        abstract_sources=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
        archive="Stiftsarchiv Schotten, Wien (http://www.schottenstift.at)",
        archive_location="Wien",
        chancellary_remarks=[
            "commissio domini imperatoris in consilio",
            "Jüngerer Dorsualvermerk mit Regest",
        ],
        comments="The diplomatic analysis is inconclusive",
        condition="Beschädigtes Pergament",
        date="1307 II 22",
        date_quote="an sand peters tage in der vasten, als er avf den stvl ze Rome gesatz wart",
        date_value=MomDate(1307, 2, 22),
        dimensions="20x20cm",
        external_link="https://example.com/charters/1",
        fond="Urkunden",
        footnotes=["Siehe RI #1234", "Abweichend von Nr. 15"],
        graphic_urls=["K.._MOM-Bilddateien._~Schottenjpgweb._~StAS__13070222-2.jpg"],
        index=["Arenga", CEI.index("Insulare Minuskel")],
        index_geo_features=["Leithagebirge", CEI.geogName("Donau")],
        index_organizations=["Bistum Passau", CEI.orgName("Erzbistum Salzburg")],
        index_persons=[
            "Hubert, der Schuster",
            CEI.persName("Antonia Müllerin, des Müllers Frau"),
        ],
        index_places=["Wien", CEI.placeName("Wiener Neustadt")],
        issued_place="Wiener Neustadt",
        issuers="Konrad von Lintz",
        language="Deutsch",
        material="Pergament",
        literature="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103",
        literature_abstracts="[RI XIII] H. 4 n. 778, in: Regesta Imperii Online, URI: http://www.regesta-imperii.de/id/1477-04-02_1_0_13_4_0_10350_778 (Abgerufen am 13.11.2016)",
        literature_depictions="ADEVA-Verlag, Die Ostarrichi-Urkunde – Luxus-Ausgabe. Ausstattung und Preise, In: ADEVA Home (2012), online unter <http://www.adeva.com/faks_detail_bibl.asp?id=127> (12.12.2012)",
        literature_editions=[
            "Urkunden der burgundischen Rudolfinger, ed. Theodor Schieffer, Monumenta Germaniae Historica, Diplomata, 2A, Regum Burgundiae e stirpe Rudolfina diplomata et acta, München 1977; in der Folge: MGH DD Burg. 103."
        ],
        literature_secondary=[
            "HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
            "HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 127, Nr. 105",
        ],
        notarial_authentication="Albertus Magnus",
        seals="2 Siegel",
        recipient="Heinrich, des Praitenvelders Schreiber",
        tradition="orig.",
        transcription="Ich Hainrich, des Praitenvelder Schreiber, [...] ze Rome gesatz wart.",
        transcription_sources="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
        witnesses=["Franz von Ehrlingen", CEI.persName("Ulrich der Schneider")],
    )
    Validator().validate_cei(charter.to_xml())


def test_writes_correct_file(tmp_path):
    d = tmp_path
    charter = Charter("1A")
    charter.to_file(d)
    out = pathlib.Path(d, "1A.cei.xml")
    assert out.is_file()
    written = etree.parse(str(out))
    Validator().validate_cei(written.getroot())


def test_add_schema_location_is_respected():
    charter = Charter("1A")
    assert (
        charter.to_xml(add_schema_location=True).get(SCHEMA_LOCATION_QNAME)
        == SCHEMA_LOCATION
    )
    assert charter.to_xml(add_schema_location=False).get(SCHEMA_LOCATION_QNAME) == None


def test_has_correct_text_abstract():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == abstract
    abstract_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert abstract_xml.text == abstract


def test_has_correct_xml_abstract():
    pers_name = "Konrad von Lintz"
    abstract = CEI.abstract(
        CEI.persName(pers_name),
        ", Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag.",
    )
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == abstract
    abstract_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert abstract_xml.text == abstract.text
    pers_name_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:persName"
    )
    assert pers_name_xml.text == pers_name


def test_has_no_abstract_for_empty_text():
    abstract = ""
    charter = Charter(id_text="1", abstract=abstract)
    assert charter.abstract == None


def test_raises_exception_for_incorrect_xml_abstract():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", abstract=incorrect_element)


def test_has_correct_charter_archive():
    archive = "Archive 1"
    charter = Charter(id_text="1", archive=archive)
    assert charter.archive == archive
    archive_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:archIdentifier/cei:arch",
    )
    assert archive_xml.text == archive


def test_has_no_archive_for_empty_text():
    archive = ""
    charter = Charter(id_text="1", archive=archive)
    assert charter.archive == None


def test_has_correct_charter_archive_settlement():
    archive_settlement = "Vienna"
    charter = Charter(id_text="1", archive_location=archive_settlement)
    assert charter.archive_location == archive_settlement
    archive_settlement_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:archIdentifier/cei:settlement",
    )
    assert archive_settlement_xml.text == archive_settlement


def test_has_no_archive_settlement_for_empty_text():
    archive_settlement = ""
    charter = Charter(id_text="1", archive_location=archive_settlement)
    assert charter.archive_location == None


def test_has_correct_abstract_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        abstract_sources=bibl_text,
    )
    assert isinstance(charter.abstract_sources, list)
    bibl = xps(charter, "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*")
    assert bibl.text == bibl_text


def test_has_no_sources_for_empty_string():
    bibl_texts = ""
    sources = xp(
        Charter(
            id_text="1",
            abstract_sources=bibl_texts,
        ),
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*",
    )
    assert len(sources) == 0


def test_has_correct_abstract_sources():
    bibl_texts = ["Bibl a", "Bibl b"]
    sources = xp(
        Charter(
            id_text="1",
            abstract_sources=bibl_texts,
        ),
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescRegest/*",
    )
    assert len(sources) == 2
    assert sources[0].text == bibl_texts[0]
    assert sources[1].text == bibl_texts[1]


def test_has_correct_transcription_source():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        transcription_sources=bibl_text,
    )
    assert isinstance(charter.transcription_sources, list)
    sources = xps(
        charter, "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*"
    )
    assert sources.text == bibl_text


def test_has_no_transcription_sources_for_empty_text():
    bibl_text = ""
    charter = Charter(
        id_text="1",
        transcription_sources=bibl_text,
    )
    assert len(charter.transcription_sources) == 0


def test_has_correct_transcription_sources():
    bibl_texts = ["Bibl a", "Bibl b"]
    sources = xp(
        Charter(
            id_text="1",
            transcription_sources=bibl_texts,
        ),
        "/cei:text/cei:front/cei:sourceDesc/cei:sourceDescVolltext/*",
    )
    assert len(sources) == 2
    assert sources[0].text == bibl_texts[0]
    assert sources[1].text == bibl_texts[1]


def test_has_correct_single_chancellary_remark():
    chancellary_remarks = "Remark"
    charter = Charter(id_text="1", chancellary_remarks=chancellary_remarks)
    assert isinstance(charter.chancellary_remarks, list)
    assert charter.chancellary_remarks[0] == chancellary_remarks
    nota = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:nota")
    assert nota.text == chancellary_remarks


def test_has_correct_chancellary_remarks_list():
    chancellary_remarks = ["Remark a", "Remark b"]
    charter = Charter(id_text="1", chancellary_remarks=chancellary_remarks)
    assert charter.chancellary_remarks == chancellary_remarks
    nota = xp(charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:nota")
    assert len(nota) == 2
    assert nota[0].text == chancellary_remarks[0]
    assert nota[1].text == chancellary_remarks[1]


def test_has_no_chancellary_remarks_for_empty_text():
    chancellary_remarks = ""
    charter = Charter(id_text="1", chancellary_remarks=chancellary_remarks)
    assert len(charter.chancellary_remarks) == 0


def test_has_correct_comments():
    comments = ["Comment a", "Comment b"]
    charter = Charter(id_text="1", comments=comments)
    assert charter.comments == comments
    paragraphs = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:p",
    )
    assert len(paragraphs) == 2
    assert paragraphs[0].text == comments[0]
    assert paragraphs[1].text == comments[1]


def test_has_no_comments_for_empty_string():
    comments = ""
    charter = Charter(id_text="1", comments=comments)
    assert len(charter.comments) == 0


def test_has_correct_charter_condition():
    condition = "Charter condition"
    charter = Charter(id_text="1", condition=condition)
    assert charter.condition == condition
    condition_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:physicalDesc/cei:condition",
    )
    assert condition_xml.text == condition


def test_has_no_condition_for_empty_text():
    condition = ""
    charter = Charter(id_text="1", condition=condition)
    assert charter.condition == None


def test_has_correct_date_range_with_99999999():
    charter = Charter(id_text="1", date="unknown", date_value=("99999999", "99999999"))
    assert charter.date == "unknown"
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "unknown"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_no_date_for_empty_text():
    charter = Charter(id_text="1", date="")
    assert charter.date == None
    assert charter.date_value == None


def test_has_no_date_for_empty_value():
    charter = Charter(id_text="1", date="unknown", date_value="")
    assert charter.date == "unknown"
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "unknown"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_date_with_99999999():
    charter = Charter(id_text="1", date="unknown", date_value="99999999")
    assert charter.date == "unknown"
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "unknown"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_date_with_99_as_month():
    charter = Charter(id_text="1", date_value="14009905")
    assert charter.date_value == (
        MomDate(1400, 1, 1),
        MomDate(1400, 12, 31),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1400-01-01 – 1400-12-31"
    assert date_xml.get("from") == "14000101"
    assert date_xml.get("to") == "14001231"


def test_has_correct_date_with_99_as_day():
    charter = Charter(id_text="1", date_value="14010299")
    assert charter.date_value == (
        MomDate(1401, 2, 1),
        MomDate(1401, 2, 28),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1401-02-01 – 1401-02-28"
    assert date_xml.get("from") == "14010201"
    assert date_xml.get("to") == "14010228"


def test_has_correct_leap_year_date_with_99_as_day():
    charter = Charter(id_text="1", date_value="14040299")
    assert charter.date_value == (
        MomDate(1404, 2, 1),
        MomDate(1404, 2, 29),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1404-02-01 – 1404-02-29"
    assert date_xml.get("from") == "14040201"
    assert date_xml.get("to") == "14040229"


def test_has_correct_julian_leap_day():
    charter = Charter(id_text="1", date_value="13000229")
    assert charter.date_value == MomDate(1300, 2, 29)
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1300-02-29"
    assert date_xml.get("value") == "13000229"


def test_has_correct_julian_leap_year_date_with_99_as_day():
    charter = Charter(id_text="1", date_value="13000299")
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300-02-01 – 1300-02-29"
    assert date_xml.get("to") == "13000229"


def test_has_correct_date_range_with_datetime():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(datetime(1300, 1, 1), datetime(1300, 12, 31)),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        MomDate(1300, 1, 1),
        MomDate(1300, 12, 31),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_datetime():
    charter = Charter(
        id_text="1",
        date="1. 1. 1300",
        date_value=datetime(1300, 1, 1),
    )
    assert charter.date == "1. 1. 1300"
    assert charter.date_value == MomDate(1300, 1, 1)
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_date_range_with_iso():
    charter = Charter(id_text="1", date="1300", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == "1300"
    assert charter.date_value == (
        MomDate(1300, 1, 1),
        MomDate(1300, 12, 31),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_iso():
    charter = Charter(id_text="1", date="12. 1. 1342", date_value="1342-01-12")
    assert charter.date == "12. 1. 1342"
    assert charter.date_value == MomDate(1342, 1, 12)
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "12. 1. 1342"
    assert date_xml.get("value") == "13420112"


def test_has_correct_date_range_with_mom_date():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(
            MomDate(1300, 1, 1),
            MomDate(1300, 12, 31),
        ),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        MomDate(1300, 1, 1),
        MomDate(1300, 12, 31),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_mom_date():
    charter = Charter(
        id_text="1",
        date="1. 1. 1300",
        date_value=MomDate(1300, 1, 1),
    )
    assert charter.date == "1. 1. 1300"
    assert charter.date_value == MomDate(1300, 1, 1)
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_empty_date():
    charter = Charter(id_text="1")
    assert charter.date == None
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "Sine dato"
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_empty_date_range_text():
    charter = Charter(id_text="1", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == None
    assert charter.date_value == (
        MomDate(1300, 1, 1),
        MomDate(1300, 12, 31),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300-01-01 – 1300-12-31"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_empty_date_text():
    charter = Charter(id_text="1", date_value="1342-01-12")
    assert charter.date == None
    assert charter.date_value == MomDate(1342, 1, 12)
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1342-01-12"
    assert date_xml.get("value") == "13420112"


def test_has_correct_empty_date_value():
    text = "Sine dato"
    charter = Charter(id_text="1", date=text)
    assert charter.date == text
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == text
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_xml_date():
    date_text = "12. 10. 1789"
    date_value = "17980101"
    date = CEI.date(date_text, {"value": date_value})
    charter = Charter(id_text="1", date=date)
    assert charter.date == date
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == date_text
    assert date_xml.get("value") == date_value


def test_has_correct_xml_date_range():
    date_text = "some time in 1789"
    date_from = "17980101"
    date_to = "17981231"
    date = CEI.dateRange(date_text, {"from": date_from, "to": date_to})
    charter = Charter(id_text="1", date=date)
    assert charter.date == date
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == date_text
    assert date_xml.get("from") == date_from
    assert date_xml.get("to") == date_to


def test_raises_exception_when_initializing_with_xml_date_and_value():
    date_value = "17980101"
    date = CEI.date("12. 10. 1789", {"value": date_value})
    charter = Charter(id_text="1", date=date, date_value=date_value)
    with pytest.raises(ValueError, match="'date' is an XML element"):
        charter.to_xml()


def test_raises_exception_for_invalid_date_value():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            date="in 1789",
            date_value="17980231",  # 31st February doesn't exist
        )


def test_raises_exception_for_invalid_date_value_in_iso_format():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            date="in 1789",
            date_value="1798-02-311",  # One additional digit
        )


def test_raises_exception_for_invalid_date_value_in_mom_format():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            date="in 1789",
            date_value="179802311",  # One additional digit
        )


def test_raises_exception_for_date_range_ending_before_start():
    with pytest.raises(ValueError, match="end before it starts"):
        Charter(
            id_text="1",
            date="in 1789",
            date_value=("17980101", datetime(1789, 12, 31)),
        )


def test_raises_exception_for_incorrect_xml_date():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", date=incorrect_element)


def test_raises_exception_when_setting_date_value_for_xml_date():
    date_from = "17980101"
    date_to = "17981231"
    date = CEI.dateRange("12. 10. 1789", {"from": date_from, "to": date_to})
    charter = Charter(id_text="1", date=date)
    charter.date_value = (date_from, date_to)
    with pytest.raises(ValueError, match="'date' is an XML element"):
        charter.to_xml()


def test_raises_exception_when_setting_xml_date_after_date_value():
    charter = Charter(id_text="1", date_value="14570315")
    charter.date = CEI.date("15. März 1457", {"value": "14570316"})
    with pytest.raises(ValueError, match="'date' is an XML element"):
        charter.to_xml()


def test_has_correct_text_date_quote():
    date_quote = "A date quote"
    charter = Charter(id_text="1", date_quote=date_quote)
    assert charter.date_quote == date_quote
    date_quote_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:quoteOriginaldatierung",
    )
    assert date_quote_xml.text == date_quote


def test_has_no_quote_for_empty_text():
    date_quote = ""
    charter = Charter(id_text="1", date_quote=date_quote)
    assert charter.date_quote == None


def test_has_correct_xml_date_quote():
    date_quote = CEI.quoteOriginaldatierung(
        "Original dating with ", CEI.sup("a"), " superscript"
    )
    charter = Charter(id_text="1", date_quote=date_quote)
    assert charter.date_quote == date_quote
    superscript_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:quoteOriginaldatierung/cei:sup",
    )
    assert superscript_xml.text == "a"


def test_raises_exception_for_incorrect_xml_date_quote():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", date_quote=incorrect_element)


def test_has_correct_charter_dimensions():
    dimensions = "Charter dimensions"
    charter = Charter(id_text="1", dimensions=dimensions)
    assert charter.dimensions == dimensions
    dimensions_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:physicalDesc/cei:dimensions",
    )
    assert dimensions_xml.text == dimensions


def test_has_no_dimensions_for_empty_text():
    dimensions = ""
    charter = Charter(id_text="1", dimensions=dimensions)
    assert charter.dimensions == None


def test_has_correct_external_url():
    external_link = "https://example.com/charters/1"
    charter = Charter(id_text="1", external_link=external_link)
    assert charter.external_link == external_link
    external_link_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:archIdentifier/cei:ref",
    )
    assert external_link_xml.get("target") == external_link


def test_has_no_external_url_for_empty_text():
    external_link = ""
    charter = Charter(id_text="1", external_link=external_link)
    assert charter.external_link == None


def test_raises_exception_for_invalid_external_link():
    localhost = "http://localhost"
    with pytest.raises(ValueError):
        Charter(id_text="1", external_link=localhost)


def test_has_correct_list_graphic_urls():
    graphic_urls = ["Figure 1.jgp", "figure_2.png"]
    charter = Charter(id_text="1", graphic_urls=graphic_urls)
    assert charter.graphic_urls == graphic_urls
    graphics_xml = xp(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:figure/cei:graphic"
    )
    assert len(graphics_xml) == 2
    assert graphics_xml[0].get("url") == graphic_urls[0]
    assert graphics_xml[1].get("url") == graphic_urls[1]


def test_has_correct_single_graphic_url():
    graphic_urls = "Figure 1.jgp"
    charter = Charter(id_text="1", graphic_urls=graphic_urls)
    assert charter.graphic_urls[0] == graphic_urls
    graphics_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:figure/cei:graphic"
    )
    assert graphics_xml.get("url") == graphic_urls


def test_has_empty_graphic_urls_for_empty_text():
    graphic_urls = ""
    charter = Charter(id_text="1", graphic_urls=graphic_urls)
    assert len(charter.graphic_urls) == 0


def test_has_correct_footnotes():
    footnotes = ["Footnote a", "Footnote b"]
    charter = Charter(id_text="1", footnotes=footnotes)
    assert charter.footnotes == footnotes
    notes = xp(
        charter,
        "/cei:text/cei:back/cei:divNotes/cei:note",
    )
    assert len(notes) == 2
    assert notes[0].text == footnotes[0]
    assert notes[1].text == footnotes[1]


def test_has_no_footnotes_for_empty_text():
    footnotes = ""
    charter = Charter(id_text="1", footnotes=footnotes)
    assert len(charter.footnotes) == 0


def test_has_correct_fond():
    fond = "Fond a"
    charter = Charter(id_text="1", fond=fond)
    assert charter.fond == fond
    fond_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:archIdentifier/cei:archFond",
    )
    assert fond_xml.text == fond


def test_has_no_fond_for_empty_text():
    fond = ""
    charter = Charter(id_text="1", fond=fond)
    assert charter.fond == None


def test_has_correct_id():
    id_text = "~!1307 II 22|23.Ⅱ"
    id_norm = "~!1307_II_22|23.Ⅱ"
    charter = Charter(id_text=id_text)
    assert charter.id_text == id_text
    assert charter.id_norm == id_norm
    idno = xps(charter, "/cei:text/cei:body/cei:idno")
    assert idno.get("id") == id_norm
    assert idno.text == id_text


def test_has_correct_id_norm():
    id_text = "1307 Ⅱ 22"
    id_norm = "1307_Ⅱ_22"
    charter = Charter(id_text=id_text, id_norm="1307 Ⅱ 22")
    assert charter.id_text == id_text
    assert charter.id_norm == id_norm
    idno = xps(charter, "/cei:text/cei:body/cei:idno")
    assert idno.get("id") == id_norm
    assert idno.text == id_text


def test_has_correct_id_norm_for_empty_text():
    id = "1307-12-01"
    charter = Charter(id_text=id, id_norm="")
    assert charter.id_norm == id


def test_has_correct_id_old():
    id_old = "123456 α"
    altIdentifier = xps(
        Charter(id_text="1307 II 22", id_old=id_old),
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:archIdentifier/cei:altIdentifier",
    )
    assert altIdentifier.text == id_old
    assert altIdentifier.get("type") == "old"


def test_has_no_id_old_for_empty_text():
    charter = Charter(id_text="1307-12-01", id_old="")
    assert charter.id_old == None


def test_raises_exception_for_missing_id():
    with pytest.raises(ValueError):
        Charter(id_text="")


def test_has_correct_index_geo_features():
    index_geo_features = [
        "Geo feature a",
        CEI.geogName("Geo feature b"),
    ]
    charter = Charter(id_text="1", index_geo_features=index_geo_features)
    assert charter.index_geo_features == index_geo_features
    geog_names_xml = xp(charter, "/cei:text/cei:back/cei:geogName")
    assert len(geog_names_xml) == 2
    assert geog_names_xml[0].text == index_geo_features[0]
    assert geog_names_xml[1].text == index_geo_features[1].text


def test_raises_exception_for_invalid_index_geo_features_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            index_geo_features=[
                CEI.persName("A person"),
                CEI.geogName("An geog name"),
            ],
        )


def test_has_correct_index_terms():
    index = [
        "Term a",
        CEI.index("Term b"),
    ]
    charter = Charter(id_text="1", index=index)
    assert charter.index == index
    index_xml = xp(charter, "/cei:text/cei:back/cei:index")
    assert len(index_xml) == 2
    assert index_xml[0].text == index[0]
    assert index_xml[1].text == index[1].text


def test_raises_exception_for_invalid_index_terms_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            index=[CEI.persName("A person"), CEI.index("An index term")],
        )


def test_has_correct_index_organizations():
    index_organizations = [
        "Organization a",
        CEI.orgName("Organization b"),
    ]
    charter = Charter(id_text="1", index_organizations=index_organizations)
    assert charter.index_organizations == index_organizations
    organization_names_xml = xp(charter, "/cei:text/cei:back/cei:orgName")
    assert len(organization_names_xml) == 2
    assert organization_names_xml[0].text == index_organizations[0]
    assert organization_names_xml[1].text == index_organizations[1].text


def test_raises_exception_for_invalid_index_organizations_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            index_organizations=[
                CEI.persName("A person"),
                CEI.orgName("An organization"),
            ],
        )


def test_has_correct_index_persons():
    index_persons = [
        "Person a",
        CEI.persName("Person b"),
        CEI.persName("Person c", {"type": "Custom Type"}),
    ]
    charter = Charter(id_text="1", index_persons=index_persons)
    assert charter.index_persons == index_persons
    pers_names_xml = xp(charter, "/cei:text/cei:back/cei:persName")
    assert len(pers_names_xml) == 3
    assert pers_names_xml[0].text == index_persons[0]
    assert pers_names_xml[1].text == index_persons[1].text
    assert pers_names_xml[2].text == index_persons[2].text
    assert pers_names_xml[2].get("type") == index_persons[2].get("type")


def test_raises_exception_for_invalid_index_persons_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            index_persons=[CEI.persName("A person"), CEI.placeName("A place")],
        )


def test_has_correct_index_places():
    index_places = [
        "Place a",
        CEI.placeName("Place b"),
    ]
    charter = Charter(id_text="1", index_places=index_places)
    assert charter.index_places == index_places
    place_names_xml = xp(charter, "/cei:text/cei:back/cei:placeName")
    assert len(place_names_xml) == 2
    assert place_names_xml[0].text == index_places[0]
    assert place_names_xml[1].text == index_places[1].text


def test_raises_exception_for_invalid_index_places_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1",
            index_places=[CEI.persName("A person"), CEI.placeName("A place")],
        )


def test_has_correct_text_issued_place():
    issued_place = "Wien"
    charter = Charter(id_text="1", issued_place=issued_place)
    assert charter.issued_place == issued_place
    issued_place_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:placeName"
    )
    assert issued_place_xml.text == issued_place


def test_has_no_issued_place_for_empty_text():
    issued_place = ""
    charter = Charter(id_text="1", issued_place=issued_place)
    assert charter.issued_place == None


def test_has_correct_xml_issued_place():
    issued_place = CEI.placeName("Wien")
    charter = Charter(id_text="1", issued_place=issued_place)
    assert charter.issued_place == issued_place
    issued_place_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:placeName"
    )
    assert issued_place_xml.text == issued_place.text


def test_raises_exception_for_incorrect_xml_issued_place():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", issued_place=incorrect_element)


def test_has_correct_abstract_with_text_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = "Konrad von Lintz"
    charter = Charter(id_text="1", abstract=abstract, issuers=issuer)
    assert charter.issuers == [issuer]
    issuer_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer


def test_has_correct_abstract_with_text_single_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = "Konrad von Lintz"
    charter = Charter(id_text="1", abstract=abstract, issuers=issuer)
    assert charter.issuers == [issuer]
    issuer_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer


def test_has_correct_abstract_with_text_list_issuer():
    abstract = (
        "Konrad von Lintz und Thomas von Gmunden, beurkunden den vorstehenden Vertrag."
    )
    issuers = ["Konrad von Lintz", "Thomas von Gmunden"]
    charter = Charter(id_text="1", abstract=abstract, issuers=issuers)
    assert isinstance(charter.issuers, list)
    assert charter.issuers == issuers
    issuer_xml = xp(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml[0].text == issuers[0]
    assert issuer_xml[1].text == issuers[1]


def test_has_correct_abstract_with_xml_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = CEI.issuer("Konrad von Lintz")
    assert isinstance(issuer, etree._Element)
    charter = Charter(id_text="1", abstract=abstract, issuers=issuer)
    assert charter.issuers == [issuer]
    issuer_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer.text


def test_has_correct_abstract_with_xml_issuer_list():
    abstract = (
        "Konrad von Lintz und Thomas von Gmunden, beurkunden den vorstehenden Vertrag."
    )
    issuers = [CEI.issuer("Konrad von Lintz"), CEI.issuer("Thomas von Gmunden")]
    charter = Charter(id_text="1", abstract=abstract, issuers=issuers)
    assert isinstance(charter.issuers, list)
    assert isinstance(charter.issuers[0], etree._Element)
    assert isinstance(charter.issuers[1], etree._Element)
    assert charter.issuers[0].text == issuers[0].text
    assert charter.issuers[1].text == issuers[1].text
    issuer_xml = xp(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml[0].text == issuers[0].text
    assert issuer_xml[1].text == issuers[1].text


def test_raises_exception_for_incorrect_xml_issuer():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", issuers=incorrect_element)


def test_raises_exception_for_incorrect_xml_issuer_list():
    incorrect_elements = [CEI.persName("A person"), CEI.persName("Another person")]
    with pytest.raises(ValueError):
        Charter(id_text="1", issuers=incorrect_elements)


def test_raises_exception_for_xml_abstract_with_issuer_at_serialization():
    charter = Charter(
        id_text="1", abstract=CEI.abstract("An abstract"), issuers="An issuer"
    )
    with pytest.raises(ValueError, match="abstract.*XML.*issuers"):
        charter.to_xml()


def test_xml_abstract_with_issuer_constraint_independent_of_assignment_order():
    c1 = Charter(id_text="1")
    c1.issuers = "An issuer"
    c1.abstract = CEI.abstract("An abstract")
    with pytest.raises(ValueError):
        c1.to_xml()

    c2 = Charter(id_text="2")
    c2.abstract = CEI.abstract("An abstract")
    c2.issuers = "An issuer"
    with pytest.raises(ValueError):
        c2.to_xml()


def test_has_correct_language():
    language = "A language"
    charter = Charter(id_text="1", language=language)
    assert charter.language == language
    language_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:lang_MOM",
    )
    assert language_xml.text == language


def test_has_no_language_for_empty_string():
    language = ""
    charter = Charter(id_text="1", language=language)
    assert charter.language == None


def test_has_correct_literature():
    literature = ["Entry 1", "Entry 2"]
    charter = Charter(id_text="1", literature=literature)
    assert charter.literature == literature
    literature_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:listBibl/cei:bibl",
    )
    assert len(literature_xml) == 2
    assert literature_xml[0].text == literature[0]
    assert literature_xml[1].text == literature[1]


def test_has_no_literature_for_empty_text():
    literature = ""
    charter = Charter(id_text="1", literature=literature)
    assert len(charter.literature) == 0


def test_has_correct_literature_abstracts():
    literature_abstracts = ["Entry 1", "Entry 2"]
    charter = Charter(id_text="1", literature_abstracts=literature_abstracts)
    assert charter.literature_abstracts == literature_abstracts
    literature_abstracts_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:listBiblRegest/cei:bibl",
    )
    assert len(literature_abstracts_xml) == 2
    assert literature_abstracts_xml[0].text == literature_abstracts[0]
    assert literature_abstracts_xml[1].text == literature_abstracts[1]


def test_has_no_literature_abstracts_for_empty_text():
    literature_abstracts = ""
    charter = Charter(id_text="1", literature_abstracts=literature_abstracts)
    assert len(charter.literature_abstracts) == 0


def test_has_correct_literature_depictions():
    literature_depictions = ["Entry 1", "Entry 2"]
    charter = Charter(id_text="1", literature_depictions=literature_depictions)
    assert charter.literature_depictions == literature_depictions
    literature_depictions_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:listBiblFaksimile/cei:bibl",
    )
    assert len(literature_depictions_xml) == 2
    assert literature_depictions_xml[0].text == literature_depictions[0]
    assert literature_depictions_xml[1].text == literature_depictions[1]


def test_has_no_literature_depictions_for_empty_text():
    literature_depictions = ""
    charter = Charter(id_text="1", literature_depictions=literature_depictions)
    assert len(charter.literature_depictions) == 0


def test_has_correct_literature_editions():
    literature_editions = ["Entry 1", "Entry 2"]
    charter = Charter(id_text="1", literature_editions=literature_editions)
    assert charter.literature_editions == literature_editions
    literature_editions_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:listBiblEdition/cei:bibl",
    )
    assert len(literature_editions_xml) == 2
    assert literature_editions_xml[0].text == literature_editions[0]
    assert literature_editions_xml[1].text == literature_editions[1]


def test_has_no_literature_editions_for_empty_text():
    literature_editions = ""
    charter = Charter(id_text="1", literature_editions=literature_editions)
    assert len(charter.literature_editions) == 0


def test_has_correct_literature_secondary():
    literature_secondary = ["Entry 1", "Entry 2"]
    charter = Charter(id_text="1", literature_secondary=literature_secondary)
    assert charter.literature_secondary == literature_secondary
    literature_secondary_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:diplomaticAnalysis/cei:listBiblErw/cei:bibl",
    )
    assert len(literature_secondary_xml) == 2
    assert literature_secondary_xml[0].text == literature_secondary[0]
    assert literature_secondary_xml[1].text == literature_secondary[1]


def test_has_no_literature_secondary_for_empty_text():
    literature_secondary = ""
    charter = Charter(id_text="1", literature_secondary=literature_secondary)
    assert len(charter.literature_secondary) == 0


def test_has_correct_material():
    material = "Material"
    charter = Charter(id_text="1", material=material)
    assert charter.material == material
    material_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:physicalDesc/cei:material",
    )
    assert material_xml.text == material


def test_has_no_material_for_empty_text():
    material = ""
    charter = Charter(id_text="1", material=material)
    assert charter.material == None


def test_has_correct_text_notarial_authentication():
    notarial_authentication = "A notarial authentication"
    charter = Charter(id_text="1", notarial_authentication=notarial_authentication)
    assert charter.notarial_authentication == notarial_authentication
    notarial_authentication_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:notariusDesc",
    )
    assert notarial_authentication_xml.text == notarial_authentication


def test_has_no_text_notarial_authentication_for_empty_text():
    notarial_authentication = ""
    charter = Charter(id_text="1", notarial_authentication=notarial_authentication)
    assert charter.notarial_authentication == None


def test_has_correct_xml_notarial_authentication():
    notarial_authentication = CEI.notariusDesc("An xml notarial authentication")
    charter = Charter(id_text="1", notarial_authentication=notarial_authentication)
    assert charter.notarial_authentication == notarial_authentication
    notarial_authentication_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:notariusDesc",
    )
    assert notarial_authentication_xml.text == notarial_authentication.text


def test_raises_exception_for_incorrect_xml_notarial_authentication():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", notarial_authentication=incorrect_element)


def test_has_correct_abstract_with_text_recipient():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    recipient = "Heinrich Müller"
    charter = Charter(id_text="1", abstract=abstract, recipient=recipient)
    assert isinstance(charter.recipient, str)
    assert charter.recipient == recipient
    recipient_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:recipient"
    )
    assert recipient_xml.text == recipient


def test_has_abstract_without_text_recipient_for_empty_text():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    recipient = ""
    charter = Charter(id_text="1", abstract=abstract, recipient=recipient)
    assert charter.recipient == None


def test_has_correct_abstract_with_xml_recipient():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    recipient = CEI.recipient("Heinrich Müller")
    assert isinstance(recipient, etree._Element)
    charter = Charter(id_text="1", abstract=abstract, recipient=recipient)
    assert isinstance(charter.recipient, etree._Element)
    assert charter.recipient.text == recipient.text
    recipient_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:recipient"
    )
    assert recipient_xml.text == recipient.text


def test_raises_exception_for_xml_abstract_with_recipient_at_serialization():
    charter = Charter(
        id_text="1", abstract=CEI.abstract("An abstract"), recipient="A recipient"
    )
    with pytest.raises(ValueError, match="abstract.*XML"):
        charter.to_xml()


def test_raises_exception_for_incorrect_xml_recipient():
    incorrect_element = CEI.issuer("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", recipient=incorrect_element)


def test_has_correct_seal_description_xml():
    seal_description = CEI.sealDesc(CEI.seal("Seal 1"), CEI.seal("Seal 2"))
    charter = Charter(id_text="1", seal_description=seal_description)
    assert charter.seal_description == seal_description
    seals_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert len(seals_xml) == 2
    assert seals_xml[0].text == "Seal 1"
    assert seals_xml[1].text == "Seal 2"


def test_has_no_seals_for_empty_text():
    charter = Charter(id_text="1", seal_description="", seals="")
    assert charter.seal_description is None
    assert charter.seals == []
    assert not xp(charter, "//cei:sealDesc")


def test_has_correct_seal_text_description():
    seal_description = "2 Siegel"
    charter = Charter(id_text="1", seal_description=seal_description)
    assert charter.seal_description == seal_description
    seals_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc"
    )
    assert seals_xml.text == seal_description


def test_has_correct_single_seal_text():
    charter = Charter(id_text="1", seals="Petschaft")
    assert charter.seals == ["Petschaft"]
    seal_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert seal_xml.text == "Petschaft"


def test_has_correct_seal_description_with_seals():
    charter = Charter(
        id_text="1",
        seal_description="3 Petschaften ahgd. in Holzkapsel",
        seals=[
            Seal(description="Petschaft", sigillant="Hans"),
            CEI.seal("Petschaft, abgefallen"),
            "Petschaft",
        ],
    )
    seal_desc = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc"
    )
    assert "".join(seal_desc.itertext()) == (
        "3 Petschaften ahgd. in Holzkapsel Petschaft Hans Petschaft, abgefallen "
        "Petschaft"
    )
    seals = xp(charter, "//cei:sealDesc/cei:seal")
    assert [seal.text for seal in seals] == [
        "Petschaft ",
        "Petschaft, abgefallen",
        "Petschaft",
    ]
    assert seals[0].xpath("cei:sigillant/text()", namespaces=CHARTER_NSS) == ["Hans"]


def test_raises_exception_for_xml_seal_description_with_seals_at_serialization():
    charter = Charter(
        id_text="1", seal_description=CEI.sealDesc("2 Siegel"), seals="Petschaft"
    )
    with pytest.raises(ValueError, match="'seal_description' is an XML element"):
        charter.to_xml()


def test_raises_exception_for_incorrect_xml_seal():
    with pytest.raises(ValueError):
        Charter(id_text="1", seals=CEI.sealDesc("2 Siegel"))


def test_has_correct_multiple_seal_text_descriptions():
    seals = ["Seal 1", "Seal 2"]
    charter = Charter(id_text="1", seals=seals)
    assert charter.seals == seals
    seals_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert len(seals_xml) == 2
    assert seals_xml[0].text == "Seal 1"
    assert seals_xml[1].text == "Seal 2"


def test_has_correct_single_seal_object():
    seals = Seal(material="A material", sigillant="A sigillant")
    charter = Charter(id_text="1", seals=seals)
    assert charter.seals == [seals]
    seals_xml = xps(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert seals_xml.xpath("cei:sealMaterial/text()", namespaces=CHARTER_NSS) == [
        "A material"
    ]
    assert seals_xml.xpath("cei:sigillant/text()", namespaces=CHARTER_NSS) == [
        "A sigillant"
    ]


def test_has_correct_multiple_seal_objects():
    seals = [
        Seal(material="Material a", sigillant="Sigillant a"),
        Seal(material="Material b", sigillant="Sigillant b"),
    ]
    charter = Charter(id_text="1", seals=seals)
    assert charter.seals == seals
    seals_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert seals_xml[0].xpath("cei:sealMaterial/text()", namespaces=CHARTER_NSS) == [
        "Material a"
    ]
    assert seals_xml[0].xpath("cei:sigillant/text()", namespaces=CHARTER_NSS) == [
        "Sigillant a"
    ]
    assert seals_xml[1].xpath("cei:sealMaterial/text()", namespaces=CHARTER_NSS) == [
        "Material b"
    ]
    assert seals_xml[1].xpath("cei:sigillant/text()", namespaces=CHARTER_NSS) == [
        "Sigillant b"
    ]


def test_has_correct_text_transcription():
    transcription = "A transcription"
    charter = Charter(id_text="1", transcription=transcription)
    assert charter.transcription == transcription
    transcription_xml = xps(charter, "/cei:text/cei:body/cei:tenor")
    assert transcription_xml.text == transcription


def test_has_no_text_transcription_for_empty_text():
    transcription = ""
    charter = Charter(id_text="1", transcription=transcription)
    assert charter.transcription == None


def test_has_correct_xml_transcription():
    transcription = CEI.tenor("Tenor with ", CEI.sup("a"), " superscript")
    charter = Charter(id_text="1", transcription=transcription)
    assert charter.transcription == transcription
    superscript_xml = xps(
        charter,
        "/cei:text/cei:body/cei:tenor/cei:sup",
    )
    assert superscript_xml.text == "a"


def test_raises_exception_for_incorrect_xml_transcription():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", transcription=incorrect_element)


def test_has_correct_tradition():
    tradition = "orig."
    charter = Charter(id_text="1", tradition=tradition)
    assert charter.tradition == tradition
    tradition_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:traditioForm"
    )
    assert tradition_xml.text == tradition


def test_has_no_tradition_for_empty_text():
    tradition = ""
    charter = Charter(id_text="1", tradition=tradition)
    assert charter.tradition == None


def test_has_correct_type():
    charter = Charter(id_text="1").to_xml()
    assert charter.get("type") == "charter"


def test_has_correct_witnesses():
    witnesses = [
        "Witness a",
        CEI.persName("Witness b"),
        CEI.persName("Witness c", {"type": "Zeuge"}),
    ]
    charter = Charter(id_text="1", witnesses=witnesses)
    assert charter.witnesses == witnesses
    pers_names_xml = xp(charter, '/cei:text/cei:back/cei:persName[@type="Zeuge"]')
    assert len(pers_names_xml) == 3
    assert pers_names_xml[0].text == witnesses[0]
    assert pers_names_xml[1].text == witnesses[1].text
    assert pers_names_xml[2].text == witnesses[2].text


def test_raises_exception_for_invalid_witnesses_xml():
    with pytest.raises(ValueError):
        Charter(
            id_text="1", witnesses=[CEI.persName("A Person"), CEI.placeName("A place")]
        )


def test_list_fields_are_not_shared_between_instances():
    c1 = Charter(id_text="1")
    c1.witnesses = ["Alice"]
    c1.literature = ["Lit A"]
    c1.abstract_sources = ["Src A"]
    c2 = Charter(id_text="2")
    assert c2.witnesses == []
    assert c2.literature == []
    assert c2.abstract_sources == []
    c1.witnesses.append("Bob")
    assert c2.witnesses == []


def test_external_link_accepts_valid_https_url():
    charter = Charter(id_text="1", external_link="https://example.org/charters/1")
    assert charter.external_link == "https://example.org/charters/1"


def test_external_link_accepts_empty_as_none():
    charter = Charter(id_text="1", external_link="")
    assert charter.external_link is None


def test_external_link_rejects_url_without_tld():
    with pytest.raises(ValueError):
        Charter(id_text="1", external_link="http://localhost")


def test_external_link_rejects_non_http_scheme():
    with pytest.raises(ValueError):
        Charter(id_text="1", external_link="ftp://example.org/x")


@pytest.mark.parametrize(
    "argument,element,xpath",
    [
        (
            "abstract_sources",
            CEI.bibl("Edition ", CEI.ref("1")),
            "//cei:sourceDescRegest/cei:bibl",
        ),
        (
            "chancellary_remarks",
            CEI.nota(CEI.expan("Registrata")),
            "//cei:witnessOrig/cei:nota",
        ),
        (
            "comments",
            CEI.p("Siehe ", CEI.persName("Konrad")),
            "//cei:diplomaticAnalysis/cei:p",
        ),
        (
            "condition",
            CEI.condition("Fleckig ", CEI.note("alt")),
            "//cei:physicalDesc/cei:condition",
        ),
        (
            "dimensions",
            CEI.dimensions(CEI.height("20"), CEI.width("30"), unit="cm"),
            "//cei:physicalDesc/cei:dimensions",
        ),
        ("footnotes", CEI.note("Vgl. ", CEI.bibl("RI")), "//cei:divNotes/cei:note"),
        (
            "graphic_urls",
            CEI.figure(CEI.graphic(url="1.jpg"), CEI.figDesc("Recto")),
            "//cei:witnessOrig/cei:figure",
        ),
        ("literature", CEI.bibl(CEI.author("Hauswirth")), "//cei:listBibl/cei:bibl"),
        (
            "literature_abstracts",
            CEI.bibl(CEI.author("Hauswirth")),
            "//cei:listBiblRegest/cei:bibl",
        ),
        (
            "literature_depictions",
            CEI.bibl(CEI.author("Hauswirth")),
            "//cei:listBiblFaksimile/cei:bibl",
        ),
        (
            "literature_editions",
            CEI.bibl(CEI.author("Hauswirth")),
            "//cei:listBiblEdition/cei:bibl",
        ),
        (
            "literature_secondary",
            CEI.bibl(CEI.author("Hauswirth")),
            "//cei:listBiblErw/cei:bibl",
        ),
        (
            "provenance",
            CEI.provenance(CEI.arch("Registratur")),
            "/cei:text/cei:front/cei:provenance",
        ),
        (
            "transcription_sources",
            CEI.bibl(CEI.author("Hauswirth")),
            "//cei:sourceDescVolltext/cei:bibl",
        ),
    ],
)
def test_writes_passed_element_unchanged(argument, element, xpath):
    charter = Charter(id_text="1", **{argument: element})
    assert etree.tostring(xps(charter, xpath)) == etree.tostring(element)


@pytest.mark.parametrize(
    "argument",
    [
        "abstract_sources",
        "chancellary_remarks",
        "comments",
        "condition",
        "dimensions",
        "footnotes",
        "graphic_urls",
        "literature",
        "provenance",
        "transcription_sources",
    ],
)
def test_raises_exception_for_wrong_passed_element(argument):
    with pytest.raises(ValueError):
        Charter(id_text="1", **{argument: CEI.idno("wrong")})  # pyright: ignore[reportArgumentType]


def test_accepts_mixed_entries_in_any_sequence():
    persons = ("Anna", CEI.persName("Berta", key="(DE-588)1"))
    charter = Charter(
        id_text="1", index_persons=persons, issuers=["Konrad", CEI.issuer("Hans")]
    )
    assert [
        person.text for person in xp(charter, "/cei:text/cei:back/cei:persName")
    ] == ["Anna", "Berta"]
    assert [issuer.text for issuer in xp(charter, "//cei:abstract/cei:issuer")] == [
        "Konrad",
        "Hans",
    ]


def test_second_to_xml_leaves_first_result_intact():
    charter = Charter(
        id_text="1", abstract=CEI.abstract("Regest von ", CEI.persName("Konrad"))
    )
    first = charter.to_xml()
    charter.to_xml()
    assert len(first.findall(".//cei:abstract/cei:persName", CHARTER_NSS)) == 1


def test_passed_element_is_not_moved_or_changed():
    parent = CEI.p(CEI.persName("Hans"), " folgt")
    witness = parent[0]
    before = etree.tostring(witness)
    xml = Charter(id_text="1", witnesses=[witness]).to_xml()
    assert witness.getparent() is parent
    assert etree.tostring(witness) == before
    copy = xml.find("cei:back/cei:persName", CHARTER_NSS)
    assert copy is not None
    assert copy.tail is None or not copy.tail.strip()


def test_has_correct_witness_type_on_passed_element():
    witness = CEI.persName("Hans", key="(DE-588)1")
    charter = Charter(id_text="1", witnesses=witness)
    witness_xml = xps(charter, "/cei:text/cei:back/cei:persName")
    assert witness_xml.get("type") == "Zeuge"
    assert witness_xml.get("key") == "(DE-588)1"
    assert witness.get("type") is None


def test_raises_exception_for_witness_with_other_type():
    with pytest.raises(ValueError, match="witness"):
        Charter(id_text="1", witnesses=CEI.persName("Hans", type="Aussteller"))


def test_has_abstract_for_issuers_without_abstract_text():
    charter = Charter(id_text="1", issuers="Konrad", recipient="Stift Schotten")
    abstract = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert [ln(child) for child in abstract] == ["issuer", "recipient"]


def test_has_issuers_and_recipient_as_mom_excel_import_writes_them():
    charter = Charter(
        id_text="1",
        abstract="Konrad und Hans verkaufen dem Stift einen Hof.",
        issuers=["Konrad", CEI.issuer("Hans")],
        recipient="Stift Schotten",
    )
    abstract = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract")
    assert etree.tostring(abstract, method="text", encoding="unicode") == (
        "Konrad und Hans verkaufen dem Stift einen Hof."
        " Aussteller: Konrad; Hans Empfänger: Stift Schotten"
    )


def test_has_correct_text_witnesses():
    witness = CEI.witness(CEI.traditioForm("cop."), CEI.archIdentifier(CEI.idno("1")))
    charter = Charter(
        id_text="1",
        text_witnesses=[
            "Kopialbuch 1, fol. 3",
            TextWitness("in Nr. 546", tradition="ins."),
            witness,
        ],
    )
    witnesses = xp(charter, "/cei:text/cei:body/cei:chDesc/cei:witListPar/cei:witness")
    assert witnesses[0].text == "Kopialbuch 1, fol. 3"
    assert witnesses[1][0].text == "ins."
    assert witnesses[1][0].tail == " in Nr. 546"
    assert etree.tostring(witnesses[2]) == etree.tostring(witness)
    Validator().validate_cei(charter.to_xml())


def test_has_text_witness_list_after_witness_orig():
    charter = Charter(id_text="1", text_witnesses="Kopialbuch 1", comments="Kommentar")
    chdesc = xps(charter, "/cei:text/cei:body/cei:chDesc")
    names = [ln(child) for child in chdesc]
    assert names.index("witListPar") == names.index("witnessOrig") + 1


def test_has_no_text_witness_list_without_entries():
    assert not xp(Charter(id_text="1", text_witnesses=""), "//cei:witListPar")


def test_raises_exception_for_wrong_text_witness_element():
    with pytest.raises(ValueError):
        Charter(id_text="1", text_witnesses=CEI.persName("Hans"))


def test_has_correct_text_provenance():
    charter = Charter(id_text="1", provenance="Registratur des Stifts")
    assert (
        xps(charter, "/cei:text/cei:front/cei:provenance").text
        == "Registratur des Stifts"
    )


def test_archive_idno_defaults_to_id_text_without_id():
    charter = Charter(id_text="1307 II 22")
    idno = xps(charter, "//cei:archIdentifier/cei:idno")
    assert idno.text == "1307 II 22"
    assert idno.get("id") is None
    assert xps(charter, "/cei:text/cei:body/cei:idno").get("id") == "1307_II_22"


def test_has_correct_archive_signature_and_internal_id():
    charter = Charter(
        id_text="1307 II 22",
        archive_signature="Urkunde 217593",
        archive_internal_id="217593",
    )
    idno = xps(charter, "//cei:archIdentifier/cei:idno")
    assert idno.text == "Urkunde 217593"
    assert idno.get("n") == "217593"
    assert idno.get("id") is None


def test_full_charter_with_new_arguments_is_valid():
    charter = Charter(
        id_text="1",
        archive_signature="Urkunde 1",
        archive_internal_id="1",
        provenance=CEI.provenance(CEI.arch("Registratur")),
        comments=["Ein Kommentar", CEI.p("Siehe ", CEI.persName("Konrad"))],
        dimensions=CEI.dimensions(CEI.height("20"), CEI.width("30"), unit="cm"),
        graphic_urls=["1.jpg", CEI.figure(CEI.graphic(url="2.jpg"))],
        seal_description="2 Petschaften",
        seals=[
            Seal(description="ahgd.", sigillant=CEI.sigillant(CEI.persName("Hans"))),
            "Petschaft",
        ],
        witnesses=["Anna", CEI.persName("Berta")],
    )
    Validator().validate_cei(charter.to_xml())


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1307 II 22", "1307_II_22"),
        ("K//1, n° 1", "K||1_n°_1"),
        ("Urk. 12 (a)", "Urk_12(a)"),
        ("I - 3", "I-3"),
        ("a?b=c:d%e#f$g", "abcdefg"),
        ("a;b", "a;b"),
        ("?", "0000"),
    ],
)
def test_mom_id_follows_mom_import_rules(text, expected):
    assert mom_id(text) == expected


@pytest.mark.parametrize("text", ["1307 II 22", "K//1, n° 1", "Urk. 12 (a)", "I - 3"])
def test_mom_id_is_unchanged_by_a_second_pass(text):
    assert mom_id(mom_id(text)) == mom_id(text)


def test_id_norm_applies_mom_id_to_explicit_value():
    assert Charter(id_text="1", id_norm="K//1, n° 1").id_norm == "K||1_n°_1"


def test_file_name_has_no_subfolder_for_slashes(tmp_path):
    Charter(id_text="K//1, n° 1").to_file(tmp_path)
    assert (tmp_path / "K||1_n°_1.cei.xml").is_file()


def test_arguments_after_id_text_are_keyword_only():
    with pytest.raises(TypeError):
        Charter("1", "Regest")  # pyright: ignore[reportCallIssue]


@pytest.mark.parametrize("id_text", [1457, None, ""])
def test_raises_exception_for_invalid_id_text(id_text):
    with pytest.raises((TypeError, ValueError), match="id_text"):
        Charter(id_text)


@pytest.mark.parametrize(
    "arguments",
    [
        {"archive": CEI.arch("Stiftsarchiv")},
        {"abstract": float("nan")},
        {"comments": 3},
        {"index_persons": [["Anna"]]},
        {"date_value": 1457},
        {"external_link": CEI.ref("https://example.org/charters/1")},
        {"id_norm": 1457},
    ],
)
def test_raises_type_error_naming_the_argument(arguments):
    (name,) = arguments
    with pytest.raises(TypeError, match=name):
        Charter("1", **arguments)


@pytest.mark.parametrize("date_value", ["5000-03-15", "-5000-03-15", "10000-01-01"])
def test_raises_exception_for_years_without_mom_value(date_value):
    with pytest.raises(ValueError, match="date_value"):
        Charter("1", date_value=date_value)


def test_accepts_date_without_time():
    from datetime import date

    assert Charter("1", date_value=date(1457, 3, 15)).date_value == MomDate(1457, 3, 15)


def test_empty_seal_next_to_xml_seal_description_is_ignored():
    charter = Charter("1", seal_description=CEI.sealDesc("2 Siegel"), seals=Seal())
    assert xps(charter, "//cei:sealDesc").text == "2 Siegel"


def test_accepts_tuple_of_text_witnesses():
    charter = Charter("1", text_witnesses=("Kopialbuch A", "Kopialbuch B"))
    witnesses = xp(charter, "//cei:witListPar/cei:witness")
    assert [witness.text for witness in witnesses] == ["Kopialbuch A", "Kopialbuch B"]


@pytest.mark.parametrize(
    "arguments,error",
    [
        ({"text": ""}, ValueError),
        ({"text": CEI.idno("1")}, TypeError),
        ({"text": "in Nr. 546", "tradition": ""}, ValueError),
    ],
)
def test_text_witness_checks_its_fields(arguments, error):
    with pytest.raises(error):
        TextWitness(**arguments)


def test_separates_the_parts_of_the_arch_identifier():
    charter = Charter(
        "1",
        archive="Stiftsarchiv",
        archive_location="Wien",
        external_link="https://example.org/1",
        fond="Urkunden",
        id_old="alt 1",
    )
    arch_identifier = xps(charter, "//cei:archIdentifier")
    assert "".join(arch_identifier.itertext()) == "Wien Stiftsarchiv Urkunden 1 alt 1"


def test_adds_no_separator_next_to_whitespace_of_a_passed_seal():
    charter = Charter(
        "1",
        seal_description="2 Siegel ",
        seals=[CEI.seal("Petschaft"), CEI.seal(CEI.sigillant("Hans"), " ")],
    )
    seal_desc = xps(charter, "//cei:sealDesc")
    assert "".join(seal_desc.itertext()) == "2 Siegel Petschaft Hans "


def test_adds_no_separator_before_a_text_witness_starting_with_whitespace():
    charter = Charter("1", text_witnesses=TextWitness(" Kopialbuch", tradition="cop."))
    witness = xps(charter, "//cei:witListPar/cei:witness")
    assert "".join(witness.itertext()) == "cop. Kopialbuch"


@pytest.mark.parametrize(
    "name,entry,error",
    [
        ("issuers", CEI.persName("Konrad"), ValueError),
        ("index_persons", 1457, TypeError),
        ("seals", CEI.sealDesc("Siegel"), ValueError),
    ],
)
def test_checks_entries_appended_in_place(name, entry, error):
    charter = Charter("1")
    getattr(charter, name).append(entry)
    with pytest.raises(error, match=name):
        charter.to_xml()


def test_checks_seals_changed_in_place():
    seal = Seal(legend="S. CONRADI")
    seal.legend.append(CEI.sigillant("Konrad"))
    with pytest.raises(ValueError, match="legend"):
        Charter("1", seals=seal).to_xml()


@pytest.mark.parametrize(
    "arguments,expected",
    [
        ({"issuers": "A", "recipient": "B"}, "Aussteller: A Empfänger: B"),
        ({"recipient": "B"}, "Empfänger: B"),
        ({"abstract": "Regest.", "issuers": "A"}, "Regest. Aussteller: A"),
        ({"abstract": "Regest. ", "issuers": "A"}, "Regest. Aussteller: A"),
        ({"abstract": "Regest.", "issuers": ["A", "B"]}, "Regest. Aussteller: A; B"),
    ],
)
def test_labels_issuers_and_recipient_without_extra_space(arguments, expected):
    abstract = xps(Charter("1", **arguments), "//cei:abstract")
    assert "".join(abstract.itertext()) == expected
