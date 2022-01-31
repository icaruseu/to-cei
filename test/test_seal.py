import pytest

from pytest_helpers import xp, xps
from to_cei.config import CEI
from to_cei.seal import Seal
from to_cei.validator import Validator


def test_is_seal_valid():
    seal = Seal(
        condition="A condotion",
        dimensions="Some dimensions",
        legend=[("recto", "The recto legend"), ("verso", "The verso legend")],
        material="A material",
        sigillant="The sigillant",
    )
    Validator().validate_cei(
        CEI.text(
            CEI.front(),
            CEI.body(
                CEI.idno("1", {"id": "1"}),
                CEI.chDesc(CEI.witnessOrig(CEI.auth(CEI.sealDesc(seal.to_xml())))),
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
    assert seal.legend == legend
    legend_xml = xps(seal, "/cei:seal/cei:legend")
    assert legend_xml.text == legend


def test_has_correct_multiple_legends():
    legends = [("recto", "The recto legend"), ("verso", "The verso legend")]
    seal = Seal(
        legend=legends,
    )
    assert seal.legend == legends
    legends_xml = xp(seal, "/cei:seal/cei:legend")
    assert len(legends_xml) == 2
    assert legends_xml[0].text == legends[0][1]
    assert legends_xml[0].get("place") == legends[0][0]
    assert legends_xml[1].text == legends[1][1]
    assert legends_xml[1].get("place") == legends[1][0]


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
    sigillant = CEI.persName("A sigillant")
    seal = Seal(sigillant=sigillant)
    assert seal.sigillant == sigillant
    sigillant_xml = xps(seal, "/cei:seal/cei:sigillant/cei:persName")
    assert sigillant_xml == sigillant


def test_raises_exception_for_wrong_sigillant_xml():
    with pytest.raises(ValueError):
        Seal(sigillant=CEI.placeName())
