from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Cabine:
    name: str
    number: str
    direction: str
    center: Tuple[float]

    @property
    def full_name(self) -> str:
        return f'{self.name}'

    def available_direction(self):
        return [self.direction]

    def get_coordinate(self, side):
        return self.center

    def s(self, side):
        s = {
            'Н': ['Лево', 'Право', 'Перед', 'Зад', 'Центр', 0, 1, lambda z1, z2: z1 > z2],
            'В': ['Лево', 'Право', 'Перед', 'Зад', 'Центр', 0, 1, lambda z1, z2: z1 < z2],
        }
        return s[side]