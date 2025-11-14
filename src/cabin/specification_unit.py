from dataclasses import dataclass, field
from typing import List

@dataclass(order=True, frozen=True)
class SpecificationUnit():
    manufacture: str
    info: str
    articul: str
    count: str
    unit: str
    name: str = field(compare=False, repr=False)
    row: int = field(compare=False, repr=False)
    column: int = field(compare=False, repr=False)
    typeplot: str = field(compare=False, repr=False)


class SpecificationUnitList(List[SpecificationUnit]):
    def get(self):
        print(self)

    def get_devices(self):
        self_filter = [d for d in self if d.typeplot[0] != '-' and d.name and d.row]
        return sorted(self_filter, key=lambda x: 10**12 * x.row + x.column)

@dataclass(frozen=True)
class AutocadTemplate():
    block_name: str
    contacts: dict
    length: int