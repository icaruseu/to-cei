import pathlib
from datetime import datetime
from typing import List

import pytest
from astropy.time.core import Time
from lxml import etree

from pytest_helpers import xp, xps
from to_cei.charter import NO_DATE_TEXT, NO_DATE_VALUE, Charter
from to_cei.config import (CEI, CHARTER_NSS, SCHEMA_LOCATION,
                           SCHEMA_LOCATION_QNAME)
from to_cei.helpers import ln
from to_cei.seal import Seal
from to_cei.validator import Validator

# --------------------------------------------------------------------#
#                         Charter as a whole                         #
# --------------------------------------------------------------------#


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
        chancellary_remarks=[
            "commissio domini imperatoris in consilio",
            "Jüngerer Dorsualvermerk mit Regest",
        ],
        comments="The diplomatic analysis is inconclusive",
        condition="Beschädigtes Pergament",
        date="1307 II 22",
        date_quote="an sand peters tage in der vasten, als er avf den stvl ze Rome gesatz wart",
        date_value=Time("1307-02-22", format="isot", scale="ut1"),
        dimensions="20x20cm",
        external_link="https://example.com/charters/1",
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
        issuer="Konrad von Lintz",
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


# --------------------------------------------------------------------#
#                          Charter abstract                          #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                          Charter archive                           #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                       Charter bibliographies                       #
# --------------------------------------------------------------------#


def test_has_correct_abstract_bibl():
    bibl_text = "Bibl a"
    charter = Charter(
        id_text="1",
        abstract_sources=bibl_text,
    )
    assert isinstance(charter.abstract_sources, List)
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
    assert isinstance(charter.transcription_sources, List)
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


# --------------------------------------------------------------------#
#                    Charter chancellary remarks                     #
# --------------------------------------------------------------------#


def test_has_correct_single_chancellary_remark():
    chancellary_remarks = "Remark"
    charter = Charter(id_text="1", chancellary_remarks=chancellary_remarks)
    assert isinstance(charter.chancellary_remarks, List)
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


# --------------------------------------------------------------------#
#                          Charter comments                          #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                         Charter condition                          #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                            Charter date                             #
# --------------------------------------------------------------------#


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
        Time("1400-01-01", format="isot", scale="ut1").ymdhms,
        Time("1400-12-31", format="isot", scale="ut1").ymdhms,
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "+01400-01-01 - +01400-12-31"
    assert date_xml.get("from") == "14000101"
    assert date_xml.get("to") == "14001231"


def test_has_correct_date_with_99_as_day():
    charter = Charter(id_text="1", date_value="14000299")
    assert charter.date_value == (
        Time("1400-02-01", format="isot", scale="ut1").ymdhms,
        Time("1400-02-28", format="isot", scale="ut1").ymdhms,
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "+01400-02-01 - +01400-02-28"
    assert date_xml.get("from") == "14000201"
    assert date_xml.get("to") == "14000228"


def test_has_correct_leap_year_date_with_99_as_day():
    charter = Charter(id_text="1", date_value="14040299")
    assert charter.date_value == (
        Time("1404-02-01", format="isot", scale="ut1"),
        Time("1404-02-29", format="isot", scale="ut1"),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "+01404-02-01 - +01404-02-29"
    assert date_xml.get("from") == "14040201"
    assert date_xml.get("to") == "14040229"


def test_has_correct_date_range_with_datetime():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(datetime(1300, 1, 1), datetime(1300, 12, 31)),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
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
    assert charter.date_value == Time("1300-01-01", format="isot", scale="ut1")
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_date_range_with_iso():
    charter = Charter(id_text="1", date="1300", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_iso():
    charter = Charter(id_text="1", date="12. 1. 1342", date_value="1342-01-12")
    assert charter.date == "12. 1. 1342"
    assert charter.date_value == Time("1342-01-12", format="isot", scale="ut1")
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "12. 1. 1342"
    assert date_xml.get("value") == "13420112"


def test_has_correct_date_range_with_Time():
    charter = Charter(
        id_text="1",
        date="1300",
        date_value=(
            Time({"year": 1300, "month": 1, "day": 1}, scale="ut1"),
            Time({"year": 1300, "month": 12, "day": 31}, scale="ut1"),
        ),
    )
    assert charter.date == "1300"
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "1300"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_date_with_Time():
    charter = Charter(
        id_text="1",
        date="1. 1. 1300",
        date_value=Time({"year": 1300, "month": 1, "day": 1}, scale="ut1"),
    )
    assert charter.date == "1. 1. 1300"
    assert charter.date_value == Time("1300-01-01", format="isot", scale="ut1")
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "1. 1. 1300"
    assert date_xml.get("value") == "13000101"


def test_has_correct_empty_date():
    charter = Charter(id_text="1")
    assert charter.date == None
    assert charter.date_value == None
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == NO_DATE_TEXT
    assert date_xml.get("value") == NO_DATE_VALUE


def test_has_correct_empty_date_range_text():
    charter = Charter(id_text="1", date_value=("1300-01-01", "1300-12-31"))
    assert charter.date == None
    assert charter.date_value == (
        Time("1300-01-01", format="isot", scale="ut1"),
        Time("1300-12-31", format="isot", scale="ut1"),
    )
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:dateRange")
    assert date_xml.text == "+01300-01-01 - +01300-12-31"
    assert date_xml.get("from") == "13000101"
    assert date_xml.get("to") == "13001231"


def test_has_correct_empty_date_text():
    charter = Charter(id_text="1", date_value="1342-01-12")
    assert charter.date == None
    assert charter.date_value == Time("1342-01-12", format="isot", scale="ut1")
    date_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:issued/cei:date")
    assert date_xml.text == "+01342-01-12"
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
    with pytest.raises(ValueError):
        Charter(id_text="1", date=date, date_value=date_value)


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


def test_raises_exception_for_incorrect_date_value_pair():
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        charter.date_value = (date_from, date_to)


# --------------------------------------------------------------------#
#                         Charter date quote                         #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                         Charter dimensions                         #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                        Charter external url                        #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                     Charter figures / graphics                     #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                         Charter footnotes                          #
# --------------------------------------------------------------------#


def test_has_correct_footnotes():
    footnotes = ["Footnote a", "Footnote b"]
    charter = Charter(id_text="1", footnotes=footnotes)
    assert charter._footnotes == footnotes
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
    assert len(charter._footnotes) == 0


# --------------------------------------------------------------------#
#                             Charter id                             #
# --------------------------------------------------------------------#


def test_has_correct_id():
    id_text = "~!1307 II 22|23.Ⅱ"
    id_norm = "~%211307%20II%2022%7C23.%E2%85%A1"
    charter = Charter(id_text=id_text)
    assert charter.id_text == id_text
    assert charter.id_norm == id_norm
    idno = xps(charter, "/cei:text/cei:body/cei:idno")
    assert idno.get("id") == id_norm
    assert idno.text == id_text


def test_has_correct_id_norm():
    id_text = "1307 Ⅱ 22"
    id_norm = "1307_%E2%85%A1_22"
    charter = Charter(id_text=id_text, id_norm="1307_Ⅱ_22")
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
    idno = xps(
        Charter(id_text="1307 II 22", id_old=id_old), "/cei:text/cei:body/cei:idno"
    )
    assert idno.get("old") == id_old


def test_has_no_id_old_for_empty_text():
    charter = Charter(id_text="1307-12-01", id_old="")
    assert charter.id_old == None


def test_raises_exception_for_missing_id():
    with pytest.raises(ValueError):
        Charter(id_text="")


# --------------------------------------------------------------------#
#                       Charter index                                #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                        Charter issued place                        #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                           Charter issuer                           #
# --------------------------------------------------------------------#


def test_has_correct_abstract_with_text_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = "Konrad von Lintz"
    charter = Charter(id_text="1", abstract=abstract, issuer=issuer)
    assert isinstance(charter.issuer, str)
    assert charter.issuer == issuer
    issuer_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer


def test_has_correct_abstract_with_empty_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = ""
    charter = Charter(id_text="1", abstract=abstract, issuer=issuer)
    assert charter.issuer == None


def test_has_correct_abstract_with_xml_issuer():
    abstract = (
        "Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag."
    )
    issuer = CEI.issuer("Konrad von Lintz")
    assert isinstance(issuer, etree._Element)
    charter = Charter(id_text="1", abstract=abstract, issuer=issuer)
    assert isinstance(charter.issuer, etree._Element)
    assert charter.issuer.text == issuer.text
    issuer_xml = xps(charter, "/cei:text/cei:body/cei:chDesc/cei:abstract/cei:issuer")
    assert issuer_xml.text == issuer.text


def test_raises_exception_for_incorrect_xml_issuer():
    incorrect_element = CEI.persName("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", issuer=incorrect_element)


def test_raises_exception_for_xml_abstract_with_issuer():
    with pytest.raises(ValueError):
        Charter(id_text="1", abstract=CEI.abstract("An abstract"), issuer="An issuer")


# --------------------------------------------------------------------#
#                          Charter language                          #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                      Charter literature lists                      #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                          Charter material                          #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                        Charter notarial authentication             #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                         Charter recipient                          #
# --------------------------------------------------------------------#


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


def test_raises_exception_for_xml_abstract_with_recipient():
    with pytest.raises(ValueError):
        Charter(
            id_text="1", abstract=CEI.abstract("An abstract"), recipient="An recipient"
        )


def test_raises_exception_for_incorrect_xml_recipient():
    incorrect_element = CEI.issuer("A person")
    with pytest.raises(ValueError):
        Charter(id_text="1", recipient=incorrect_element)


# --------------------------------------------------------------------#
#                     Charter seal descriptions                      #
# --------------------------------------------------------------------#


def test_has_correct_seal_description_xml():
    seals = CEI.sealDesc(CEI.seal("Seal 1"), CEI.seal("Seal 2"))
    charter = Charter(id_text="1", seals=seals)
    assert charter.seals == seals
    seals_xml = xp(
        charter,
        "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc/cei:seal",
    )
    assert len(seals_xml) == 2
    assert seals_xml[0].text == "Seal 1"
    assert seals_xml[1].text == "Seal 2"


def test_has_no_seal_description_for_empty_text():
    charter = Charter(id_text="1", seals="")
    assert charter.seals == None


def test_has_correct_seal_text_description():
    seals = "2 Siegel"
    charter = Charter(id_text="1", seals=seals)
    assert charter.seals == seals
    seals_xml = xps(
        charter, "/cei:text/cei:body/cei:chDesc/cei:witnessOrig/cei:auth/cei:sealDesc"
    )
    assert seals_xml.text == seals


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
    assert charter.seals == seals
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


# --------------------------------------------------------------------#
#                       Charter transcription                        #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                       Charter tradition form                       #
# --------------------------------------------------------------------#


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


# --------------------------------------------------------------------#
#                            Charter type                            #
# --------------------------------------------------------------------#


def test_has_correct_type():
    charter = Charter(id_text="1").to_xml()
    assert charter.get("type") == "charter"


# --------------------------------------------------------------------#
#                         Charter witnesses                          #
# --------------------------------------------------------------------#


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
