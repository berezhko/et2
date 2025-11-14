import math
from typing import List, Tuple, Iterator

from . import lisp_template


class Autocad:
    def autocad(self):
        return None

    def init_function(self):
        return ''  # f';; "{str(type(self))}"\n'


class Point:
    def __init__(self, point: List[float]):
        self.x = point[0]
        self.y = point[1]
        self.z = point[2] if len(point) == 3 else 0

    def __str__(self) -> str:
        return f"{self.x} {self.y} {self.z}" if self.z else f"{self.x} {self.y}"


class Text(Autocad):
    def __init__(
        self,
        point: List[float],
        text: str,
        size: float = 2,
        angle: float = 0,
        justify: str = "",
        style: str = "Standard",
    ):
        self.point = Point(point)
        self.text = text
        self.size = size
        self.angle = angle
        self.justify = justify
        self.style = style

    # ToDo сравнить вывод обоих вариантов через autocad
    def autocad_old(self) -> str:
        justify = ""
        if self.justify != "":
            justify = f' "_Justify" "{self.justify}"'
        return f'(command "_text"{justify} \'({self.point}) {self.size} {self.angle} "{self.text}")\n'

    def autocad(self) -> str:
        # Сопоставление строкового выравнивания с кодами DXF 72 и 73
        align_map = {
            "": (0, 0),     # "Left"
            "_L": (0, 0),   # "Left"
            "_C": (1, 0),   # "Center"
            "_R": (2, 0),   # "Right"
            "_A": (3, 0),   # "Aligned"
            "_M": (4, 0),   # "Middle"
            "_F": (5, 0),   # "Fit"
            "_B": (0, 0),   # "Baseline"
            "_BL": (0, 1),  # "BottomLeft"
            "_BC": (1, 1),  # "BottomCenter"
            "_BR": (2, 1),  # "BottomRight"
            "_ML": (0, 2),  # "MiddleLeft"
            "_MC": (1, 2),  # "MiddleCenter"
            "_MR": (2, 2),  # "MiddleRight"
            "_TL": (0, 3),  # "TopLeft"
            "_TC": (1, 3),  # "TopCenter"
            "_TR": (2, 3),  # "TopRight"
        }
        h_align, v_align = align_map.get(self.justify, (0, 0))

        # Угол в радианах
        angle_rad = math.radians(self.angle)

        # Начинаем формировать список DXF-кодов
        dxf = [
            '(entmake (list',
            '  (cons 0 "TEXT")',
            '  (cons 100 "AcDbEntity")',
            '  (cons 100 "AcDbText")',
            f'  (cons 10 (list {self.point.x} {self.point.y} {self.point.z}))',
            f'  (cons 40 {self.size})',
            f'  (cons 50 {angle_rad})',
            f'  (cons 1 "{self.text}")',
            f'  (cons 72 {h_align})',
            f'  (cons 73 {v_align})',
            f'  (cons 7 "{self.style}")',
        ]

        # Если выравнивание не "Left"/Baseline, нужно задать точку выравнивания (11)
        if h_align != 0 or v_align != 0:
            dxf.append(f'  (cons 11 (list {self.point.x} {self.point.y} {self.point.z}))')
        if self.style != 'Standard':
            dxf.append(f'  (cons 41 (get-style-width "{self.style}"))')

        dxf.append('))')
        return "".join(dxf) + "\n"

    def init_function(self):
        return lisp_template.get_style_width(str(type(self)))


class Mtext(Autocad):
    def __init__(self, point1, point2, text, size=2, justify=''):
        self.point1 = Point(point1)
        self.point2 = Point(point2)
        self.text = text
        self.size = size
        self.justify = justify

    def autocad(self) -> str:
        justify = ''
        height = ''
        if self.justify != '':
            justify = f' "_Justify" "{self.justify}" "Колонки" "В"'
        if self.size != '':
            height = f' "_Height" {self.size}'
        return f'(command "_mtext" \'({self.point1}){justify}{height} \'({self.point2}) "{self.text}" "")\n'


class Line(Autocad):
    def __init__(self, *points: List[float], c: bool = False):
        if len(points) < 2:
            raise Exception(points, "Недостаточно точек для построения линии")
        self.points: List[Point] = []
        for p in points:
            self.points.append(Point(p))
        self.c = c

    # ToDo сравнить вывод обоих вариантов через autocad
    def autocad_old(self) -> str:
        result = '(command "_line" '
        for point in self.points:
            result += f"'({point}) "
        if self.c:
            result += '"_c")\n'
        else:
            result += '"")\n'
        return result


    def autocad(self) -> str:
        # Количество вершин
        num_points = len(self.points)

        # Флаг замкнутости: 1 — замкнута, 0 — открыта
        flag = 1 if self.c else 0

        # Начало entmake для LWPOLYLINE
        lines = [
            "(entmake (list",
            '  (cons 0 "LWPOLYLINE")',
            '  (cons 100 "AcDbEntity")',
            '  (cons 100 "AcDbPolyline")',
            f"  (cons 90 {num_points})",   # количество вершин
            f"  (cons 70 {flag})",         # флаг замкнутости
            # Опционально: толщина, слой и т.д. можно добавить
        ]

        # Добавляем координаты вершин (только X, Y — Z не используется в LWPOLYLINE)
        for p in self.points:
            x = p.x
            y = p.y
            lines.append(f"  (cons 10 (list {x} {y}))")

        lines.append("))")
        return "".join(lines) + "\n"


class PolyLine(Autocad):
    def __init__(self, *points: List[float], w: Tuple[float] = (0, 0), c: bool = False):
        if len(points) < 2:
            raise Exception(points, "Недостаточно точек для построения линии")
        self.points: List[Point] = []
        for p in points:
            self.points.append(Point(p))
        self.w_begin, self.w_end = w
        self.c = c

    def autocad(self) -> str:
        result = '(command "_pline" '
        for i, point in enumerate(self.points):
            result += f"'({point}) "
            if self.w_begin == self.w_end:
                if i == 0:
                    result += f'"_w" {self.w_begin} {self.w_end} '
            else:
                result += f'"_w" {self.w_begin} {self.w_end} '
        if self.c:
            result += '"_c")\n'
        else:
            result += '"")\n'
        return result


class Circle(Autocad):
    def __init__(self, point: List[float], radius: float):
        self.point = Point(point)
        self.radius = radius

    def autocad(self) -> str:
        return f'(command "_circle" \'({self.point}) {self.radius})\n'


class TextStyle(Autocad):
    def __init__(self, style: str):
        self.style = style

    def autocad(self) -> str:
        return f'(command "_TEXTSTYLE" "{self.style}")\n'


class Block(Autocad):
    def __init__(self, point: List[float], name: str, angle=0):
        self.point = Point(point)
        self.name = name
        self.angle = angle

    def autocad(self) -> str:
        return f'(command "_insert" "{self.name}" \'({self.point}) 1 1 {self.angle})\n'


class Layer(Autocad):
    def __init__(self, name, color = 7):
        self.layer = name
        self.color = color

    def autocad(self) -> str:
        return f'(SetLayer "{self.layer}" {self.color} 0)\n'

    def init_function(self) -> str:
        return lisp_template.set_layer(str(type(self)))

TypeElement = Line | PolyLine | Text | Circle | Block | TextStyle | Layer


class AutocadElements(List[TypeElement]):
    def _elements_to_autocad(self, elements: List[TypeElement]) -> str:
        result = ""
        for el in elements:
            result += el.autocad()
        return result

    def _runplot(self, list_functions: List[str]) -> str:
        result = "(defun c:runplot (/)\n"
        for func in list_functions:
            result += f" (c:{func})\n"
        result += ")\n"
        return result

    def _get_shrink_elements(self) -> Iterator[List[TypeElement]]:
        COUNT_LINES = 1000
        result = []
        for i, e in enumerate(self, start=1):
            result.append(e)
            if (i % COUNT_LINES) == 0:
                yield result
                result = []
        if result:
            yield result

    def _get_function(self, func_name: str, elements: List[TypeElement]) -> str:
        result = f"(defun c:{func_name} (/)\n"
        result += self._elements_to_autocad(elements)
        result += ")\n"
        return result

    def save(self, file_name: str) -> None:
        result = ""
        list_functions = []
        already_initialized = set()
        for element in self:
            element_type = str(type(element))
            if element_type in already_initialized:
                continue
            result += element.init_function()
            already_initialized.add(element_type)
        for i, elements in enumerate(self._get_shrink_elements()):
            func_name = f"section{i}"
            result += self._get_function(func_name, elements)
            list_functions.append(func_name)
        result += self._runplot(list_functions)
        with open(file_name, "w+", encoding="cp1251") as f:
            f.write(result)
