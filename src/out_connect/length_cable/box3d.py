from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Box3D():
    center: Tuple[float]
    left: Tuple[float] = field(repr=False)  # От объекте вдоль ряда А к оси 0
    right: Tuple[float] = field(repr=False)  # От объекте вдоль ряда А к оси 60
    front: Tuple[float] = field(repr=False)  # От объекте вдоль оси 0 к ряду А
    rear: Tuple[float] = field(repr=False)  # От объекте вдоль оси 0 к ряду В
    down: Tuple[float] = field(repr=False)  # От объекте к отметке 0
    up: Tuple[float] = field(repr=False)  # От объекте к отметке 10000
    full_name: int


    def available_direction(self):
        return ['Лево', 'Право', 'Перед', 'Зад', 'Низ', 'Верх']

    def get_coordinate(self, side):
        result = None
        match side:
            case 'Лево':
                result = self.left
            case 'Право':
                result = self.right
            case 'Перед':
                result = self.front
            case 'Зад':
                result = self.rear
            case 'Низ':
                result = self.down
            case 'Верх':
                result = self.up
        return result

    def s(self, side):
        s = {
            'Лево': ['Перед', 'Зад', 'Низ', 'Верх', 'Право', 1, 2, lambda x, y: True],
            'Право': ['Перед', 'Зад', 'Низ', 'Верх', 'Лево', 1, 2, lambda x, y: True],
            'Перед': ['Лево', 'Право', 'Низ', 'Верх', 'Зад', 0, 2, lambda x, y: True],
            'Зад': ['Лево', 'Право', 'Низ', 'Верх', 'Перед', 0, 2, lambda x, y: True],
            'Низ': ['Лево', 'Право', 'Перед', 'Зад', 'Верх', 0, 1, lambda x, y: True],
            'Верх': ['Лево', 'Право', 'Перед', 'Зад', 'Низ', 0, 1, lambda x, y: True],
        }
            
        return s[side]


class Box3DList(List[Box3D]):
    def to_dict(self):
        result = {}
        for box in self:
            result[box.full_name] = {
                'Центр': box.center,
                'Лево': box.left,
                'Право': box.right,
                'Перед': box.front,
                'Зад': box.rear,
                'Низ': box.down,
                'Верх': box.up,
            }
        return result


    # Генерируем массив кондитатов соседей (потом из них выберем одного соседа в find_neighbour)
    def array_with_suitable_boxs(self, center, side):
        first_border = side[0]
        second_border = side[1]
        three_border = side[2]
        four_border = side[3]
        opposite_side = side[4]
        coordinate_first = side[5]  # По какой координате сравниваем (0 - по Х, 1 - по У, 2 - по Z)
        coordinate_second = side[6]  # По какой координате сравниваем (0 - по Х, 1 - по У, 2 - по Z)
        checker = side[7]  # Актуально только для контактов, для них Верхний монтаж смотрим только верхние короба, а Нижний монтаж - только нижние короба
        
        b = []
        index = []
        for j, box in self.to_dict().items():
            if (
                self._box_appropriate(box[first_border], box[second_border], center, box['Центр'], coordinate_first, checker) and 
                self._box_appropriate(box[three_border], box[four_border], center, box['Центр'], coordinate_second, checker)
            ):
                b.append(box[opposite_side])
                index.append(j)
        self._try_check_array_neighbour(b, center, side)  # Не должно быть нулевого результата, в хуждем случае будут юнит найдет и вернет себя
        return b, index
    
    
    def _try_check_array_neighbour(self, b, center_contact, side):
        if len(b) == 0:
            raise Exception(center_contact, side)
    
    
    # Подходит ли нам сосед для включения его в массив проверки
    def _box_appropriate(self, first_border, second_border, checked_center, opposite_center, coordinate, checker):
        result = False

        if first_border[coordinate] <= checked_center[coordinate] < second_border[coordinate]:
            if checker(checked_center[2], opposite_center[2]):
                result = True
        return result