from lxml import etree

from to_cei.config import CEI_NS


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


def ln(element: etree._Element) -> str:
    """Get the local name of an element."""
    return etree.QName(element.tag).localname


def ns(element: etree._Element) -> str:
    """Get the namespace of an element."""
    return etree.QName(element.tag).namespace


def get_str(value: str | None = None) -> str | None:
    return value if value is not None and len(value) else None


def get_str_list(value: str | list[str] | None = None) -> list[str]:
    if value is None or (isinstance(value, str) and not len(value)):
        return []
    return list(value) if isinstance(value, list) else [value]


def get_str_or_element(
    value: str | etree._Element | None, *tags: str
) -> str | etree._Element | None:
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
    values: list[str | etree._Element] | None, *tags: str
) -> list[str | etree._Element]:
    result = []
    if values is not None:
        for value in values:
            value = get_str_or_element(value, *tags)
            if value is not None:
                result.append(value)
    return result
