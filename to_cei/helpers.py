from typing import List, Optional

from lxml import etree

from to_cei.config import CEI_NS


def join(
    *values: Optional[etree._Element | List[etree._Element]],
) -> List[etree._Element]:
    """Joins all non-empty values in a list."""
    all = []
    for value in values:
        if isinstance(value, etree._Element):
            all.append(value)
        elif isinstance(value, List) and len(value):
            all = all + value
    return all


def ln(element: etree._Element) -> str:
    """Get the local name of an element."""
    return etree.QName(element.tag).localname


def ns(element: etree._Element) -> str:
    """Get the namespace of an element."""
    return etree.QName(element.tag).namespace


def get_str(value: Optional[str] = None) -> Optional[str]:
    return value if value is not None and len(value) else None


def get_str_list(value: Optional[str | List[str]] = []) -> List[str]:
    return (
        []
        if value is None or (isinstance(value, str) and not len(value))
        else (value if isinstance(value, List) else [value])
    )


def get_str_or_element(
    value: Optional[str | etree._Element], *tags: str
) -> Optional[str | etree._Element]:
    if isinstance(value, str) and not len(value):
        return None
    if isinstance(value, etree._Element):
        if ns(value) != CEI_NS:
            raise ValueError(
                "Provided element needs to be in the CEI namespace but instead is in '{}'".format(
                    ns(value)
                )
            )
        if ln(value) not in tags:
            raise ValueError(
                "Provided element needs to be one of '{}', but instead is '{}'".format(
                    ", ".join(tags), ln(value)
                )
            )
    return value


def get_str_or_element_list(
    values: Optional[List[str | etree._Element]], *tags: str
) -> List[str | etree._Element]:
    result = []
    if values is not None:
        for value in values:
            value = get_str_or_element(value, *tags)
            if value is not None:
                result.append(value)
    return result
