import copy
from collections.abc import Callable, Sequence
from typing import Any, overload

from lxml import etree

from to_cei.config import CEI_NS

type TextOrElement = str | etree._Element | None
type Entries = str | etree._Element | Sequence[str | etree._Element] | None

XML_WHITESPACE = frozenset(" \t\n\r")


def join(
    *values: etree._Element | list[etree._Element] | None,
) -> list[etree._Element]:
    """Joins all non-empty values in a list."""
    all = []
    for value in values:
        if isinstance(value, etree._Element):
            all.append(value)
        elif isinstance(value, list) and len(value):
            all = all + value
    return all


def text_of(part: str | etree._Element) -> str:
    """The text a reader sees in `part`, without the tail of an element."""
    return part if isinstance(part, str) else "".join(part.itertext())


def runs_together(before: str, after: str) -> bool:
    """Whether two texts would read as one word without a separator."""
    return bool(
        before
        and after
        and before[-1] not in XML_WHITESPACE
        and after[0] not in XML_WHITESPACE
    )


def separated(*parts: str | etree._Element | None) -> list[str | etree._Element]:
    """The parts of a mixed-content element, with a space between two texts
    that would otherwise run together.

    Missing parts are left out. A space goes between two neighbouring texts
    unless the first ends or the second starts with XML whitespace. A part
    without text, such as an element with only attributes, gets none, and
    the texts on either side of it count as neighbours.
    """
    result: list[str | etree._Element] = []
    previous = ""
    for part in parts:
        if part is None:
            continue
        text = text_of(part)
        if runs_together(previous, text):
            result.append(" ")
        result.append(part)
        if text:
            previous = text
    return result


def ln(element: etree._Element) -> str:
    """Get the local name of an element."""
    return etree.QName(element).localname


def ns(element: etree._Element) -> str | None:
    """Get the namespace of an element."""
    return etree.QName(element).namespace


def get_str(value: str | None = None) -> str | None:
    """Text, or None for missing. Empty text counts as missing."""
    if value is not None and not isinstance(value, str):
        raise TypeError(f"expected text, got {type(value).__name__}")
    return value or None


def required_text(value: str) -> str:
    """`value`, which must be non-empty text."""
    check_text(value)
    return value


def check_text(value: object, name: str | None = None, optional: bool = False) -> None:
    """Raise unless `value` is non-empty text, or None where `optional`.
    A `name` prefixes the error message."""
    prefix = f"{name}: " if name else ""
    if optional and value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{prefix}expected text, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{prefix}must not be empty")


def get_str_or_element(value: TextOrElement, *tags: str) -> str | etree._Element | None:
    """Text, or a CEI element with one of `tags`. Empty text counts as missing."""
    if value is None or isinstance(value, str):
        return value or None
    if not isinstance(value, etree._Element):
        raise TypeError(f"expected text or a CEI element, got {type(value).__name__}")
    if ns(value) != CEI_NS:
        raise ValueError(
            "Provided element needs to be in the CEI namespace but instead "
            f"is in '{ns(value)}'"
        )
    if ln(value) not in tags:
        raise ValueError(
            f"Provided element needs to be one of '{', '.join(tags)}', "
            f"but instead is '{ln(value)}'"
        )
    return value


def get_entries(value: Any, *tags: str, kinds: tuple[type, ...] = ()) -> list[Any]:
    """One entry or a sequence of entries. Each entry is text, a CEI element
    with one of `tags`, or an instance of one of `kinds`. Empty texts are
    dropped."""
    if value is None or isinstance(value, (str, etree._Element, *kinds)):
        items = [value]
    elif isinstance(value, Sequence):
        items = list(value)
    else:
        raise TypeError(f"expected an entry or a sequence, got {type(value).__name__}")
    entries = []
    for item in items:
        entry = item if isinstance(item, kinds) else get_str_or_element(item, *tags)
        if entry is not None:
            entries.append(entry)
    return entries


def copy_element(element: etree._Element) -> etree._Element:
    """A copy of a passed element for the output, so building never moves
    or changes the caller's element. The tail belongs to the element's
    old parent and is dropped."""
    duplicate = copy.deepcopy(element)
    duplicate.tail = None
    return duplicate


@overload
def build(
    value: str | etree._Element, maker: Callable[[str], etree._Element]
) -> etree._Element: ...


@overload
def build(value: None, maker: Callable[[str], etree._Element]) -> None: ...


@overload
def build(
    value: TextOrElement, maker: Callable[[str], etree._Element]
) -> etree._Element | None: ...


def build(
    value: TextOrElement, maker: Callable[[str], etree._Element]
) -> etree._Element | None:
    """The element `maker` builds from text, or a copy of a passed element."""
    if value is None:
        return None
    if isinstance(value, etree._Element):
        return copy_element(value)
    return maker(value)
