import pytest
from lxml import etree

from pytest_helpers import xp, xps
from to_cei.config import CEI
from to_cei.helpers import ln
from to_cei.seal import Legend, Seal
from to_cei.validator import Validator


def test_is_seal_valid():
    seal = Seal(
        condition="A condotion",
        dimensions="Some dimensions",
        legend=[
            Legend("The recto legend", place="recto"),
            Legend("The verso legend", place="verso"),
        ],
        material="A material",
        sigillant="The sigillant",
    )
    seal_xml = seal.to_xml()
    assert seal_xml is not None
    Validator().validate_cei(
        CEI.text(
            CEI.front(),
            CEI.body(
                CEI.idno("1", {"id": "1"}),
                CEI.chDesc(CEI.witnessOrig(CEI.auth(CEI.sealDesc(seal_xml)))),
            ),
            CEI.back(),
            {"type": "charter"},
        )
    )


def test_correctly_returns_no_xml_for_empty_seal():
    assert Seal().to_xml() is None


def test_has_correct_condition():
    condition = "A condition"
    seal = Seal(
        condition=condition,
    )
    assert seal.condition == condition
    condition_xml = xps(seal, "/cei:seal/cei:sealCondition")
    assert condition_xml.text == condition


def test_has_correct_dimensions():
    dimensions = "A dimension"
    seal = Seal(
        dimensions=dimensions,
    )
    assert seal.dimensions == dimensions
    dimensions_xml = xps(seal, "/cei:seal/cei:sealDimensions")
    assert dimensions_xml.text == dimensions


def test_has_correct_single_legend():
    legend = "A single legend"
    seal = Seal(
        legend=legend,
    )
    assert seal.legend == [legend]
    legend_xml = xps(seal, "/cei:seal/cei:legend")
    assert legend_xml.text == legend


def test_has_correct_multiple_legends():
    legends = (
        Legend("The recto legend", place="recto"),
        Legend("The verso legend", place="verso"),
    )
    seal = Seal(
        legend=legends,
    )
    assert seal.legend == list(legends)
    legends_xml = xp(seal, "/cei:seal/cei:legend")
    assert [(entry.text, entry.get("place")) for entry in legends_xml] == [
        ("The recto legend", "recto"),
        ("The verso legend", "verso"),
    ]


def test_has_correct_material():
    material = "A material"
    seal = Seal(
        material=material,
    )
    assert seal.material == material
    material_xml = xps(seal, "/cei:seal/cei:sealMaterial")
    assert material_xml.text == material


def test_has_correct_text_sigillant():
    sigillant = "A sigillant"
    seal = Seal(
        sigillant=sigillant,
    )
    assert seal.sigillant == sigillant
    sigillant_xml = xps(seal, "/cei:seal/cei:sigillant")
    assert sigillant_xml.text == sigillant


def test_has_correct_xml_sigillant():
    sigillant = CEI.sigillant(CEI.persName("A sigillant"), " und Konvent")
    seal = Seal(sigillant=sigillant)
    assert seal.sigillant is sigillant
    sigillant_xml = xps(seal, "/cei:seal/cei:sigillant")
    assert sigillant_xml is not sigillant
    assert etree.tostring(sigillant_xml) == etree.tostring(sigillant)


@pytest.mark.parametrize("element", [CEI.placeName(), CEI.persName("A sigillant")])
def test_raises_exception_for_wrong_sigillant_xml(element):
    with pytest.raises(ValueError):
        Seal(sigillant=element)


def test_has_correct_description_before_structured_parts():
    seal = Seal(description="ahgd., in Holzkapsel", material="Wachs")
    seal_xml = seal.to_xml()
    assert seal_xml is not None
    assert "".join(seal_xml.itertext()) == "ahgd., in Holzkapsel Wachs"
    assert [ln(child) for child in seal_xml] == ["sealMaterial"]


def test_has_correct_description_only():
    seal_xml = Seal(description="Petschaft").to_xml()
    assert seal_xml is not None
    assert seal_xml.text == "Petschaft"
    assert len(seal_xml) == 0


def test_has_correct_mixed_legends():
    legend = CEI.legend("S(IGILLUM) ", CEI.expan("CONRADI"))
    seal = Seal(legend=["A legend", Legend("The verso legend", place="verso"), legend])
    legends_xml = xp(seal, "/cei:seal/cei:legend")
    assert [entry.text for entry in legends_xml] == [
        "A legend",
        "The verso legend",
        "S(IGILLUM) ",
    ]
    assert legends_xml[1].get("place") == "verso"
    assert etree.tostring(legends_xml[2]) == etree.tostring(legend)


def test_raises_exception_for_wrong_legend_xml():
    with pytest.raises(ValueError):
        Seal(legend=CEI.sigillant("A sigillant"))


def test_accepts_tuple_of_legend_texts():
    seal = Seal(legend=("Recto legend", "Verso legend"))
    assert [entry.text for entry in xp(seal, "/cei:seal/cei:legend")] == [
        "Recto legend",
        "Verso legend",
    ]


@pytest.mark.parametrize(
    "arguments,error",
    [
        ({"text": ""}, ValueError),
        ({"text": None}, TypeError),
        ({"text": "S. CONRADI", "place": ""}, ValueError),
        ({"text": "S. CONRADI", "place": 1}, TypeError),
    ],
)
def test_legend_checks_its_fields(arguments, error):
    with pytest.raises(error):
        Legend(**arguments)


def test_arguments_are_keyword_only():
    with pytest.raises(TypeError):
        Seal("beschädigt")  # pyright: ignore[reportCallIssue]


def test_raises_type_error_with_argument_name():
    with pytest.raises(TypeError, match="material"):
        Seal(material=CEI.sealMaterial("Wachs"))  # pyright: ignore[reportArgumentType]


def test_writes_parts_in_schema_order():
    seal = Seal(
        condition="beschädigt",
        description="ahgd.",
        dimensions="15 mm",
        legend="S. CONRADI",
        material="Wachs",
        sigillant="Konrad",
    )
    seal_xml = seal.to_xml()
    assert seal_xml is not None
    assert (
        "".join(seal_xml.itertext()) == "ahgd. Konrad S. CONRADI 15 mm Wachs beschädigt"
    )
    assert [ln(child) for child in seal_xml] == [
        "sigillant",
        "legend",
        "sealDimensions",
        "sealMaterial",
        "sealCondition",
    ]
