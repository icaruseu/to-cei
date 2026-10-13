from collections.abc import Sequence
from dataclasses import dataclass

from lxml import etree

from to_cei._fields import Field, check_fields
from to_cei.config import CEI
from to_cei.helpers import (
    TextOrElement,
    build,
    check_text,
    get_entries,
    get_str,
    get_str_or_element,
    separated,
)


@dataclass(frozen=True)
class Legend:
    """A seal legend with the place where it appears, written as
    `cei:legend[@place]`.

    Raises:
        TypeError: if `text` or `place` isn't text.
        ValueError: if `text` or `place` is empty.
    """

    text: str
    place: str | None = None

    def __post_init__(self) -> None:
        check_text(self.text, "text")
        check_text(self.place, "place", optional=True)


type LegendEntry = str | Legend | etree._Element


def _get_legends(
    value: LegendEntry | Sequence[LegendEntry] | None,
) -> list[LegendEntry]:
    return get_entries(value, "legend", kinds=(Legend,))


def _norm_sigillant(value: TextOrElement) -> str | etree._Element | None:
    return get_str_or_element(value, "sigillant")


def _legend(entry: LegendEntry) -> etree._Element:
    if isinstance(entry, Legend):
        if entry.place is None:
            return CEI.legend(entry.text)
        return CEI.legend(entry.text, {"place": entry.place})
    return build(entry, CEI.legend)


class Seal:
    condition: Field[str | None] = Field(get_str)
    description: Field[str | None] = Field(get_str)
    dimensions: Field[str | None] = Field(get_str)
    legend: Field[list[LegendEntry]] = Field(_get_legends)
    material: Field[str | None] = Field(get_str)
    sigillant: Field[str | etree._Element | None] = Field(_norm_sigillant)

    def __init__(
        self,
        *,
        condition: str | None = None,
        description: str | None = None,
        dimensions: str | None = None,
        legend: LegendEntry | Sequence[LegendEntry] | None = None,
        material: str | None = None,
        sigillant: TextOrElement = None,
    ) -> None:
        """A single seal, written as `cei:seal` inside `cei:sealDesc`.

        All arguments are keyword-only. Empty strings count as missing. A
        passed element is written as a copy and never changed.

        Args:
            condition: The seal's condition, as `cei:sealCondition`.
            description: Free text at the start of `cei:seal`, before the
                structured parts, such as how the seal is attached or its
                container ("ahgd., in Holzkapsel").
            dimensions: The seal's dimensions, as `cei:sealDimensions`.
            legend: One legend or a sequence of them. Each is a text, a
                `Legend` that also gives the place where it appears, or a
                complete `cei:legend` element.
            material: The seal's material, as `cei:sealMaterial`.
            sigillant: The sigillant as text or a complete `cei:sigillant`
                element, for example one wrapping a `cei:persName`.

        Raises:
            TypeError: if a value has the wrong type.
            ValueError: if an element isn't the expected CEI element.
        """
        self.condition = condition
        self.description = description
        self.dimensions = dimensions
        self.legend = legend
        self.material = material
        self.sigillant = sigillant

    def to_xml(self) -> etree._Element | None:
        """The seal as `cei:seal`, or None if no field is set.

        Raises:
            TypeError: if a value changed in place, such as an entry appended
                to `legend`, has the wrong type.
            ValueError: if a value changed in place isn't the expected CEI
                element.
        """
        check_fields(self)
        # cei:seal allows any order, so the parts follow the schema's
        # declaration order.
        children = []
        if self.sigillant is not None:
            children.append(build(self.sigillant, CEI.sigillant))
        children += [_legend(entry) for entry in self.legend]
        if self.dimensions is not None:
            children.append(CEI.sealDimensions(self.dimensions))
        if self.material is not None:
            children.append(CEI.sealMaterial(self.material))
        if self.condition is not None:
            children.append(CEI.sealCondition(self.condition))
        parts = separated(self.description, *children)
        return CEI.seal(*parts) if parts else None
