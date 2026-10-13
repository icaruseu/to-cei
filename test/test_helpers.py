import itertools

import pytest
from lxml import etree

from to_cei.config import CEI, CEI_NS
from to_cei.helpers import (
    XML_WHITESPACE,
    copy_element,
    get_entries,
    join,
    ln,
    ns,
    separated,
    text_of,
)


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


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, []),
        ("", []),
        ("Anna", ["Anna"]),
        (["Anna", "", "Berta"], ["Anna", "Berta"]),
        (("Anna",), ["Anna"]),
    ],
)
def test_gets_entries_from_text(value, expected):
    assert get_entries(value, "persName") == expected


def test_gets_entries_with_elements():
    element = CEI.persName("Berta")
    assert get_entries(element, "persName") == [element]
    assert get_entries(["Anna", element], "persName") == ["Anna", element]


def test_raises_exception_for_wrong_entry_element():
    with pytest.raises(ValueError):
        get_entries(["Anna", CEI.placeName("Wien")], "persName")


def test_raises_exception_for_entry_outside_cei_namespace():
    with pytest.raises(ValueError):
        get_entries(etree.Element("persName"), "persName")


def test_copies_element_without_tail():
    parent = CEI.p(CEI.persName("Anna"), " folgt")
    element = parent[0]
    duplicate = copy_element(element)
    assert duplicate is not element
    assert duplicate.tail is None
    assert element.tail == " folgt"
    assert element.getparent() is parent


def _reading(parts):
    return "".join(text_of(part) for part in parts)


def _ends(text):
    return CEI.p(CEI.hi("x"), text)


SAMPLES = [
    "a",
    " a",
    "a ",
    "a\n",
    "a ",
    CEI.p("a"),
    CEI.p(" a "),
    _ends("a "),
    _ends("a"),
    CEI.ref({"target": "https://example.org"}),
]


@pytest.mark.parametrize(
    "parts,expected",
    [
        (("a", "b"), "a b"),
        (("a ", "b"), "a b"),
        (("a", " b"), "a b"),
        (("a\n", "b"), "a\nb"),
        (("a ", "b"), "a  b"),
        (("a", None, "b"), "a b"),
        ((CEI.p("a"), CEI.p("b")), "a b"),
        ((_ends("a "), CEI.p("b")), "xa b"),
        ((CEI.p("a"), CEI.ref({"target": "x"}), CEI.p("b")), "a b"),
        ((CEI.ref({"target": "x"}), "b"), "b"),
        ((), ""),
    ],
)
def test_separates_texts_that_would_run_together(parts, expected):
    assert _reading(separated(*parts)) == expected


def test_separator_sits_between_the_parts():
    first, second = CEI.p("a"), CEI.p("b")
    assert separated(first, None, second) == [first, " ", second]


@pytest.mark.parametrize("parts", list(itertools.product(SAMPLES, repeat=3)))
def test_separates_only_where_texts_would_run_together(parts):
    inputs = [part for part in parts if part is not None]
    matched = 0
    texted: list[tuple[str, bool]] = []
    separator = False
    for item in separated(*parts):
        if matched < len(inputs) and item is inputs[matched]:
            matched += 1
            if text := text_of(item):
                texted.append((text, separator))
                separator = False
        else:
            assert item == " " and not separator
            separator = True
    assert matched == len(inputs) and not separator
    assert not texted or not texted[0][1]
    for (before, _), (after, separated_before) in itertools.pairwise(texted):
        at_whitespace = before[-1] in XML_WHITESPACE or after[0] in XML_WHITESPACE
        assert separated_before != at_whitespace
