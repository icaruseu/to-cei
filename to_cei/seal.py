from typing import List, Optional, Tuple

from lxml import etree

from to_cei.config import CEI
from to_cei.helpers import validate_element
from to_cei.xml_assembler import XmlAssembler


class Seal(XmlAssembler):
    _condition: Optional[str] = None
    _dimensions: Optional[str] = None
    _legend: Optional[str] | List[Tuple[str, str]] = []
    _material: Optional[str] = None
    _sigillant: Optional[str | etree._Element] = None

    def __init__(
        self,
        condition: str = None,
        dimensions: str = None,
        legend: str | List[Tuple[str, str]] = [],
        material: str = None,
        sigillant: str | etree._Element = None,
    ) -> None:
        """
        Creates a seal instance.

        Parameters:
        -----------
        condition: A description of the seal's condition.

        dimensions: A description of the seal's dimensions.

        legend: The seals legend or legends. Can bei either a text or a list of tuples of two strings where the first one is the place of the legend and the second the legend itselfself.

        material: A description of the seal's material.

        sigillant: The sigillant of the seal, either as a text or an etree._Element that contains either a cei:persName or a cei:orgName.
        """
        self.condition = condition
        self.dimensions = dimensions
        self.legend = legend
        self.material = material
        self.sigillant = sigillant

    # --------------------------------------------------------------------#
    #                             Properties                             #
    # --------------------------------------------------------------------#

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value: str = None):
        self._condition = value

    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value: str = None):
        self._dimensions = value

    @property
    def legend(self):
        return self._legend

    @legend.setter
    def legend(self, value: str | List[Tuple[str, str]] = []):
        self._legend = value

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value: str = None):
        self._material = value

    @property
    def sigillant(self):
        return self._sigillant

    @sigillant.setter
    def sigillant(self, value: str | etree._Element = None):
        self._sigillant = validate_element(value, "persName", "orgName")

    # --------------------------------------------------------------------#
    #                           Public methods                           #
    # --------------------------------------------------------------------#

    def to_xml(self) -> Optional[etree._Element]:
        children = []
        if self.condition is not None:
            children.append(CEI.sealCondition(self.condition))
        if self.dimensions is not None:
            children.append(CEI.sealDimensions(self.dimensions))
        if isinstance(self.legend, str):
            children.append(CEI.legend(self.legend))
        if isinstance(self.legend, List):
            children = children + [
                CEI.legend(legend[1], {"place": legend[0]}) for legend in self.legend
            ]
        if self.material is not None:
            children.append(CEI.sealMaterial(self.material))
        if self.sigillant is not None:
            children.append(CEI.sigillant(self.sigillant))
        return CEI.seal(*children) if len(children) else None
