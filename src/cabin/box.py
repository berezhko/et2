from dataclasses import dataclass, field
from typing import List, Tuple

from src.exception import NotFoundNeighbour


@dataclass
class Box():
    center: Tuple[float]
    left: Tuple[float] = field(repr=False)
    right: Tuple[float] = field(repr=False)
    down: Tuple[float] = field(repr=False)
    up: Tuple[float] = field(repr=False)
    full_name: int

    @property
    def width(self):
        return self.right[0] - self.left[0]

    @property
    def height(self):
        return self.up[1] - self.down[1]

    def available_direction(self):
        return ['Лево', 'Право', 'Низ', 'Верх']

    def get_coordinate(self, side):
        result = None
        match side:
            case 'Лево':
                result = self.left
            case 'Право':
                result = self.right
            case 'Низ':
                result = self.down
            case 'Верх':
                result = self.up
        return result

    def s(self, side):
        s = {'Лево': ['Низ', 'Верх', 'Право', 1, lambda x, y: True],  # Смотрим между Низ и Верх, только Право, у-ковую координату, подойдут все х 
             'Право': ['Низ', 'Верх', 'Лево', 1, lambda x, y: True],  # Смотрим между Низ и Верх, только Лево, у-ковую координату, подойдут все х 
             'Низ': ['Лево', 'Право', 'Верх', 0, lambda x, y: True],  # Смотрим между Лево и Право, только Верх, х-ковую координату, подойдут все у 
             'Верх': ['Лево', 'Право', 'Низ', 0, lambda x, y: True],  # Смотрим между Лево и Право, только Низ, х-ковую координату, подойдут все у 
            }
        return s[side]


class BoxList(List[Box]):
    def to_dict(self):
        result = {}
        for box in self:
            result[box.full_name] = {
                'Центр': box.center,
                'Лево': box.left,
                'Право': box.right,
                'Низ': box.down,
                'Верх': box.up,
            }
        return result


    # Генерируем массив кондитатов соседей (потом из них выберем одного соседа в find_neighbour)
    def array_with_suitable_boxs(self, center, side):
        first_border = side[0]
        second_border = side[1]
        opposite_side = side[2]
        coordinate = side[3]  # По какой координате сравниваем (0 - по Х, 1 - по У)
        checker = side[4]  # Актуально только для контактов, для них Верхний монтаж смотрим только верхние короба, а Нижний монтаж - только нижние короба
        
        b = []
        index = []
        for j, box in self.to_dict().items():
            if self._box_appropriate(box[first_border], box[second_border], center, box['Центр'], coordinate, checker):
                b.append(box[opposite_side])
                index.append(j)
        self._try_check_array_neighbour(b, center, side)
        return b, index
    
    
    def _try_check_array_neighbour(self, b, center_contact, side):
        if len(b) == 0:
            raise NotFoundNeighbour(center_contact, side)
    
    
    # Подходит ли нам сосед для включения его в массив проверки
    def _box_appropriate(self, first_border, second_border, checked_center, opposite_center, coordinate, checker):
        result = False
        inverse = lambda x: 0 if x == 1 else 1
        if first_border[coordinate] <= checked_center[coordinate] < second_border[coordinate]:
            if checker(checked_center[inverse(coordinate)], opposite_center[inverse(coordinate)]):
                result = True
        return result