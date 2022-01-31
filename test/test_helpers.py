from lxml import etree

from to_cei.config import CEI, CEI_NS
from to_cei.helpers import join, ln, ns


def test_gets_correct_local_name():
    assert ln(CEI.text()) == "text"


def test_gets_correct_namespace():
    assert ns(CEI.text()) == CEI_NS


def test_joins_correctly():
    joined = join(
        CEI.text(), None, CEI.persName(), None, [], [CEI.placeName(), CEI.persName()]
    )
    assert len(joined) == 4
    assert etree.tostring(joined[0]) == etree.tostring(CEI.text())
    assert etree.tostring(joined[1]) == etree.tostring(CEI.persName())
    assert etree.tostring(joined[2]) == etree.tostring(CEI.placeName())
    assert etree.tostring(joined[3]) == etree.tostring(CEI.persName())
