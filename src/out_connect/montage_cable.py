# ## Функции построения монтажных схем

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict
from sys import stderr

from src.elements import Line as Line
from src.elements import Text as Text

from src.station.misc import get_long_cabinet_name
from src.station.misc import get_short_cabinet_name
from src.misc import safe_excel_writer
from src.out_connect.direction import is_direction

from src.exception import NotFoundCable
from src.exception import NotFoundDirection
from src.exception import TerminalIsBusy
from src.exception import ReferenceToCableIncorect
from src.exception import CableIsBusy


station = None
contact_data = None
cables_collection = None
clemmnic_data = None

# ### describe_cabin

def describe_cabin(cell, begin_x, offset_y):
    x = begin_x
    y = offset_y
    font_size = 2.5
    title = get_long_cabinet_name(station, int(cell.cabin))
    return [Text((x, y + 4+font_size), title, font_size)]


# ### plot_border

def plot_border(cell, offset_x, offset_y):
    x = offset_x
    y = offset_y
    title = get_short_cabinet_name(station, int(cell.cabin)) + " " + cell.clemmnic
    result = [
        Line((x + 0, y + 4), (x + 50, y + 4)),
        Text((x + 25, y + 2), title, 2, 0, '_MC'),
        Line((x + 0, y + 4), (x + 0, y - 4*cell.count_clemms())),
        Line((x + 20, y + 0), (x + 20, y - 4*cell.count_clemms())),
        Line((x + 30, y + 0), (x + 30, y - 4*cell.count_clemms())),
        Line((x + 50, y + 4), (x + 50, y - 4*cell.count_clemms())),
    ]
    return result


# ### plot_table

def plot_table(cell, offset_x, offset_y):
    result = []
    for i in range(cell.count_clemms()):
        x = offset_x
        y = offset_y -i*4
        
        result += [
            Line((x, y), (x+50, y))
        ]
        clemma = station.get_clemma(cell.first+i, cell.cabin, cell.clemmnic)

        wire_outside, device_inside = get_wire_and_device(cell, clemma)

        result += [
            Text((x+25, y-2), clemma, 2, 0, '_MC')
        ]
        if wire_outside != "":
            result += [
                Text((x+10, y-2), wire_outside, 2, 0, '_MC')
            ]
        if device_inside != "":
            result += [
                Text((x+40, y-2), device_inside, 2, 0, '_MC')
            ]
            
    y = offset_y - 4*cell.count_clemms()
    result += [
        Line((x, y), (x+50, y))
    ]
    
    return result


# ### plot_jumper

def plot_arrow(x, y, direction):
    if direction == 'up':
        sign = 4
    elif direction == 'down':
        sign = -4
    result = [
        Line((x, y), (x, y+sign)),
        Line((x-0.5, y), (x, y+sign)),
        Line((x+0.5, y), (x, y+sign)),
    ]
    return result

# Сторона перемычек определяется для всего клеммника.
# Если хотябы одна жила имеет левую перемычку в клеммнике,
# то все перемычки будут левыми!
# ToDo Добавить проверку на жилы (get_depth_jumpers тоже должен учитывать направления)!
def get_side_jumper(cell):
    right_jumper_possition = (50, 1)
    left_jumper_possition = (0, -1)

    if is_left_jumper(cell):
        result = left_jumper_possition
    else:
        result = right_jumper_possition
    return result

def is_left_jumper(cell):
    result = False
    jumped_wires = cell.get_jumped_wires()
    
    for direction in station.left_jumper():
        cabin, clemmnic, wire = direction.split(':')
        if cabin == cell.cabin and clemmnic == cell.clemmnic and wire in jumped_wires:
            result = True
            break
    return result

def plot_jumper(cell, offset_x, offset_y):
    first, last = cell.first, cell.last
    result = []
    x = offset_x
    
    depth_jumpers = get_depth_jumpers(cell.get_jumped_wires())
    length_jumper = 3
    for depth in map(int, depth_jumpers.keys()):
        
        for jumper in depth_jumpers[str(depth)]:
            start_possition, sign = get_side_jumper(cell)
            x = offset_x + start_possition + sign*length_jumper*depth
            
            length = len(jumper)
            for i, clemm in enumerate(jumper):
                y = offset_y - clemm*4 + 4*(first-1)
                
                # Горизонтальные линии
                # Первая перемычка всегда косая внех
                if i == 0:
                    if first <= clemm and clemm < last: 
                        result += [
                            Line((x - sign*length_jumper*depth, y+2), (x, y+1))
                        ]
                # Последующие перемычки косая вверх и косая вниз
                elif 0 < i and i < (length-1):
                    if first <= clemm and clemm < last:
                        result += [
                            Line((x - sign*length_jumper*depth, y+2), (x, y+3)),
                            Line((x - sign*length_jumper*depth, y+2), (x, y+1)),
                        ]
                # Последняя перемычка всегда косая вверх
                else:
                    if first <= clemm and clemm < last:
                        result += [
                            Line((x - sign*length_jumper*depth, y+2), (x, y+3))
                        ]
                
                # Вертикальные линии
                if i > 0:
                    prev_clemm = jumper[i-1]
                    # Вертикальные линии чертим от текущей к предыдущей клемме
                    # Предыдущая клемма находится на одной монтажке с текущей клеммой
                    if first <= clemm and clemm < last and first <= prev_clemm and prev_clemm < last:
                        y1 = offset_y - prev_clemm*4 + 4*(first-1)
                        result += [Line((x, y1+1),  (x, y+3))]
                    # Предыдущая клемма находится на предудущей монтажке (стрелка вверх)
                    elif first <= clemm and clemm < last and prev_clemm < first:
                        y1 = offset_y + 4
                        result += [Line((x, y1+2), (x, y+3))]
                        result = result + plot_arrow(x, y1+2, 'up')
                    # Предыдущая клемма находится на текущей монтажке, а текущая клемма на следующей монтажке (стрелка вниз).
                    # В этом случае текущая клемма не будет рисоваться, а стрелка до нее прорисуется
                    elif first <= prev_clemm and prev_clemm < last and clemm >= last:
                        y2 = offset_y - last*4 + 4*(first-1)
                        y1 = offset_y - prev_clemm*4 + 4*(first-1)
                        result = result + plot_arrow(x, y2+2, 'down')
                        result += [Line((x, y1+1), (x, y2+2))]
    return result


# ### plot_wires

def get_points_for_describe_cable(count, n, first, last, offset_x, offset_y, right):
    return get_points(count, n, first, last, offset_x, offset_y, right)

def get_cable_plus_type(cable):
    preset_cables = station.preset_cables()
    cable_plus_type = cable
    # Для кабелей из моего раздела
    if cables_collection.cable_exist(cable):
        section, type_cab = cables_collection.section(cable)
        wire_used = cables_collection.count_used_wires(cable)
        count_wires_in_cab = cables_collection.count_wires(cable)
        cable_type = type_cab + ' ' + count_wires_in_cab + 'x' + str(section)
        cable_plus_type = cable + "  " + cable_type
    # Для прочих кабелей
    elif preset_cables.exist(cable):
        exist = '  '
        if cable in preset_cables.get_marked_cables():
            notes = preset_cables.get_notes(cable)
            exist = f" ({notes})  "
        cable_plus_type = cable + exist + preset_cables.get_full_type(cable)
    return cable_plus_type

def get_project_code(cable):
    result = ""
    preset_cables = station.preset_cables()
    if preset_cables.exist(cable):
        result = f"(см. {preset_cables.get_section(cable)})"
    return result

def describe_cable(count, n, first, last, offset_x, offset_y, cable, desc, right):
    x, y = get_points_for_describe_cable(count, n, first, last, offset_x, offset_y, right)
    
    # Экран
    result = [
        Line((x+1, y+1), (x+1, y-1)),
        Line((x-1, y+1), (x-1, y-1)),
    ]
    
    cable_full_name = desc
    cable_plus_type = get_cable_plus_type(cable)

    result += [
        Text((x+1.5-0.35, y-5), cable_full_name, 1.5, -90),
        Text((x-3.0-0.35, y-5), cable_plus_type, 1.9, -90),
        Line((x, y), (x, y-26))
    ]
    if get_project_code(cable):
        result += [
            Text((x-6.0-0.35, y-5), get_project_code(cable), 1.5, -90)
        ]
    return result

def get_points_for_plot_ground(count, n, first, last, offset_x, offset_y, right):
    return get_points(count, n, first, last, offset_x, offset_y, right)

def plot_ground(count, n, first, last, offset_x, offset_y, right):
    x , y = get_points_for_plot_ground(count, n, first, last, offset_x, offset_y, right)
    # Заземление экрана
    result = [
        Line((x-1, y), (x-3, y)),
        Line((x-3, y+3), (x-3, y-3)),
        Line((x-3-1.5, y+2), (x-3-1.5, y-2)),
        Line((x-3-3.0, y+1), (x-3-3.0, y-1)),
    ]
    return result


def in_right_side(cable, cabin):
    result = False
    
    data = get_transit_cable()
    key = cabin + ":" + cable
    
    if key in data.keys():
        result = True
    return result


# Возврящаем словарь {ШКАФ:КАБЕЛЬ, .. } с информацией о том в каких шкафал какие кабели нужно подключить справа
def get_transit_cable():
    result = {}
    for full_direction in station.transit_direction():
        cabin_cable = get_cable_by_direction(full_direction)
        result[cabin_cable] = 1
    return result


def get_cable(el):
    for c in el.keys(): # el - содержит 1 кабель со списком клемм, куда он подключается, for не переберает кабеля, а просто берет один.
        return c

def get_count_cable_in_left_side(Y, cabin):
    total_count_cable = len(Y)
    count_cable_right = 0
    for el in Y:
        cable = get_cable(el)
        if in_right_side(cable, cabin):
            count_cable_right = count_cable_right + 1
                
    return total_count_cable - count_cable_right

def check_if_wire_second(clems_used, clem):
    double_wire = 0
    if clem in clems_used.keys():
        double_wire = 1 # На 1 ниже при втором подключении
    else:
        clems_used[clem] = 1 # Отмечаем клемму для повторного подключения
    return double_wire


def get_points_for_plot_wire(count, n, first, last, i, offset_x, offset_y, double_wire, right):
    y = [offset_y -2-double_wire-(i-first)*4, offset_y -(last-first)*4-10]

    if right == False:
        x = [offset_x +0, offset_x -10*(count-n)]
        result = [x[0], x[1]+2, x[1], x[1]], [y[0], y[0], y[0]-2, y[1]]
    elif right == True: # для правых кабелей
        x = [offset_x +50, offset_x +50 +10*(count-n)] 
        result = [x[0], x[1]-2, x[1], x[1]], [y[0], y[0], y[0]-2, y[1]]

    return result

def plot_wire(count, n, first, last, i, offset_x, offset_y, double_wire, right):
    x, y = get_points_for_plot_wire(count, n, first, last, i, offset_x, offset_y, double_wire, right)
    
    result = [
        Line((x[0], y[0]), (x[1], y[1])),
        Line((x[1], y[1]), (x[2], y[2])),
        Line((x[2], y[2]), (x[3], y[3])),
    ]
    return result


def plot_wires(cell, montage_cell, offset_x, offset_y, cables_ground, cable_in_multiply_cell):
    preset_cables = station.preset_cables()
    Y = cell.Y
    first = cell.first
    last = cell.last
    
    total_count_cable = len(Y)

    # Ссылки на кабеля в других листах
    cps = [] #cables_in_previous_sheet
    cns = [] # cables_in_next_sheet

    # Смотрим какие кабеля используются в монтажках (либо другой клеммник, либо тотже клемник но на другой странице)
    check_previous_cells = True
    for temp_cell in montage_cell:
        if temp_cell == cell:
            check_previous_cells = False
            continue
        for cable in reference_to_other_cable(Y, temp_cell.Y):
            if check_previous_cells:
                cps.append(cable)
            else:
                cns.append(cable)
            
    for cable in [i for cs in [cps, cns] for i in cs]:
        if cable not in cable_in_multiply_cell:
            cable_in_multiply_cell[cable] = []

    result = []
    clems_used_left = {}
    clems_used_right = {}

    n_right = 0
    n_left = 0

    count_cable_left = get_count_cable_in_left_side(Y, cell.cabin)
    count_cable_right = total_count_cable - count_cable_left

    for total_n, el in enumerate(Y):
        cable = get_cable(el) # название кабеля
        right = in_right_side(cable, cell.cabin) # Если кабель должен отходить справа

        increment = lambda c, n: (c, n, n+1)
        if right:
            count_cable, n, n_right = increment(count_cable_right, n_right)
        else:
            count_cable, n, n_left = increment(count_cable_left, n_left)
        
        double_wire = 0
        for clem in el[cable]:
            if right:
                double_wire = check_if_wire_second(clems_used_right, clem)
            else:
                double_wire = check_if_wire_second(clems_used_left, clem)
            result = result + plot_wire(count_cable, n, first, last, station.get_number(clem, cell.cabin, cell.clemmnic), offset_x, offset_y, double_wire, right)

        # Чертим ссылку на кабель в других монтажках
        if cable in cps:  # Если наш кабель также присутствовал в предыдущих монтажках
            result = result + plot_reference_to_another_column(count_cable, n, first, last, offset_x, offset_y, right, cable, 'previous', cable_in_multiply_cell)
        if cable in cns:  # Если наш кабель также будет присутствовать в будущих монтажках
            result = result + plot_reference_to_another_column(count_cable, n, first, last, offset_x, offset_y, right, cable, 'next', cable_in_multiply_cell)

        back_cabin = cables_collection.get_back_cabin_by_cable(cell.cabin, cable)

        long_name_back_cabin = get_long_cabinet_name(station, int(back_cabin))
        result = result + describe_cable(count_cable, n, first, last, offset_x, offset_y, cable, long_name_back_cabin, right)
        # Если земля нарисована в другом шкафу или кабель существующий, то не рисум землю
        if cable not in cables_ground and cable not in preset_cables.get_marked_cables():
            result = result + plot_ground(count_cable, n, first, last, offset_x, offset_y, right)
            cables_ground[cable] = 1
    return result


# ### Разное

def get_montage_in_range(y, first, last, cabin, clemmnic):
    result = []
    for n, el in enumerate(y):
        cable = get_cable(el)
        clem_list = []
        for clem in el[cable]:
            clem_num = station.get_number(clem, cabin, clemmnic) 
            if first <= clem_num and clem_num < last:
                clem_list.append(clem)
        if len(clem_list) > 0:
            result.append({cable: clem_list})
    return result


def reference_to_other_cable(y1, y2):
    result = []
    for el1 in y1:
        cab1 = get_cable(el1)
        for el2 in y2:
            cab2 = get_cable(el2)
            if cab1 == cab2:
                if cab2 not in result:
                    result.append(cab1)
    return result


def first_and_last_plus_1(clemmnic_list, cabin, clemmnic):
    Min, Max = (10000, 0)
    for clem in clemmnic_list.keys():
        clem_number = station.get_number(clem, cabin, clemmnic)
        if clem_number > Max:
            Max = clem_number
        if clem_number < Min:
            Min = clem_number
    return (Min, Max+1)


# direction == '04:#1234:XA1:X1', или явно '16:4GG-108'
# Возврящаем ШКАФ:КАБЕЛЬ
def get_cable_by_direction(full_direction):
    info = full_direction.split(':')
    cabin = info[0]
    result = -1
    if is_direction(info[1]):
        direction_and_closets = full_direction[3:]
        cable = cables_collection.find_cable_by_direction(direction_and_closets)
        if cable != 0:
            result = cabin + ':' + cable
    else:
        result = full_direction

    if result == -1:
        raise NotFoundCable(full_direction, "По направлению не найден кабель!")

    return result


# get_depth_jumpers(cell.get_jumped_wires())
# Вход -  {'CT2-': [2, 5, 6], '2200': [8, 10, 18, 20, 28, 30, 32, 33], 'CP2-': [12, 15, 16], 'CP209': [17, 34], 'CQ2-': [22, 25, 26]}
# Выход - {'1': [[2, 5, 6], [8, 10, 18, 20, 28, 30, 32, 33]], '2': [[12, 15, 16], [17, 34]], '3': [[22, 25, 26]]}
def get_depth_jumpers(jumped_wires):
    result = {}
    for wire in jumped_wires:
        jumped_clemms = jumped_wires[wire]
        for i in range(1, len(jumped_wires)+1):
            depth = str(i) # Проверяем подходит ли данная глубина для нашей перемычки клемм (jumped_clemms)
            if depth in result:
                # Наша первая клемма в перемычке (jumped_clemms) больше последней клемма последней перемычки для данной глубины. 
                if result[depth][-1][-1] < jumped_clemms[0]: 
                    result[depth].append(jumped_clemms) # Глубина подошла, вставляем нашу перемычку последней
                    break
            else: # Ни одна глубина нам не подошла, значим опускаемся еще ниже и инициализируем следующий уровень глубины нашей перемычкой (jumped_clemms)
                result[depth] = []
                result[depth].append(jumped_clemms)
                break
    return result


# Координа на точку от которой вычисляются координаты точки для прорисовке ссылок
def get_points_for_plot_reference(count, n, first, last, offset_x, offset_y, right):
    return get_points(count, n, first, last, offset_x, offset_y, right)

# Чертим ссылки на другие листы (левые выше и в лево, правые ниже и вправо).
# Запоминаем координаты точки для вставки текста с информацией о листе
def plot_reference_to_another_column(count, n, first, last, offset_x, offset_y, right, cable, direct, cable_in_multiply_cell):
    x, y = get_points_for_plot_reference(count, n, first, last, offset_x, offset_y, right)
    index = 0
    for i, c in enumerate(cable_in_multiply_cell.keys(), start=1):
        if c == cable:
            index = i
            break
    if index == 0:
        raise NotFoundCable(cable, cable_in_multiply_cell, "Кабель в массиве cable_in_multiply_cell не найден (index == 0)!")

    if direct == 'previous':
        x1, y1, x2, y2, x3, y3 = x, y+6, x-2, y+8, x-5, y+8
    elif direct == 'next':
        x1, y1, x2, y2, x3, y3 = x, y+2, x+2, y+4, x+5, y+4
    cable_in_multiply_cell[cable].append((x3, y3))
    result = [
        Line((x1, y1), (x2, y2)),
        Line((x2, y2), (x3, y3)),
    ]
    return result

# Вставляе номер странице где еще используется данный кабель в монтажде
def plot_sheet_with_same_cable(height, cable_in_multiply_cell):
    def get_page_number(x):
        return int((x+height)/height)

    result = []
    for cable in cable_in_multiply_cell:
        ref_position = cable_in_multiply_cell[cable]
        if (len(ref_position) % 2) != 0:
            raise ReferenceToCableIncorect(ref_position, cable, "Не корректно определились ссылки на кабель!")
        for i in range(0, len(ref_position), 2):
            x1, y1 = ref_position[i]
            x2, y2 = ref_position[i+1]
            page1 = get_page_number(x1)
            page2 = get_page_number(x2)
            result += [
                Text((x1, y1), f"см л.{page2}", 1.96, 0, "_BC"),
                Text((x2, y2), f"см л.{page1}", 1.96, 0, "_BC"),
            ]
    return result

def get_points(count, n, first, last, offset_x, offset_y, right):
    y = offset_y -(last-first)*4 - 10
    if right == False:
        x = offset_x -10*(count-n)
    elif right == True: # для правых кабелей
        x = offset_x +50 +10*(count-n) 
    return x, y


# ### MontageCell

# Класс монтажной ячейки (единицы)
@dataclass(order=True)
class MontageCell():
    cabin: str
    clemmnic: str
    X: Dict = field(compare=False)
    Y: Dict = field(compare=False)
    first: int
    last: int

    def count_cable(self):
        return len(self.Y)

    def get_size(self):
        width_x = (10*self.count_cable()+50) + 20       # Ширена монтажки глеммника (20 - мин расстояние до след. клеммника по X)
        height_y = (4*(self.last-self.first) + 70) + 20 # Высота монтажки клеммника (20 - мин расстояние до след. клеммника по Y,
                                                        # 70 - высота текста подписи кабеля)
                                                        # 4 - высота строки ячеек в монтажке
                                                        # 10 - расстояние между кабелями в монтажке
        return (width_x, height_y)

    def count_clemms(self):
        return self.last - self.first

    # cell.get_jumped_wires()
    # {'CT2-': [2, 5, 6], '2200': [8, 10, 18, 20, 28, 30, 32, 33], 'CP2-': [12, 15, 16], 'CP209': [17, 34], 'CQ2-': [22, 25, 26]}
    def get_jumped_wires(self):
        X = {} # - Аналогично cell.X, только клеммы переведены в числа и отсортированы по возрастанию
        for i in sorted(map(lambda x: station.get_number(x, self.cabin, self.clemmnic), self.X.keys())):
            try:
                X[i] = self.X[station.get_clemma(i, self.cabin, self.clemmnic)]
            except Exception:
                print(i, self.cabin, self.clemmnic)
                raise
    
        result = {}
        for clemm in X:
            out_wire = X[clemm][0] # Внешняя жила указана первой в массива
            in_wire = X[clemm][1] # Внутренняя жила второй
    
            wire = in_wire if station.select_inner_jumper(self.cabin, self.clemmnic) else out_wire # Выбераем по внешним или внутренним жилам строим перемычки
            
            if wire == '': # Если жила у клемма не указана, пропускаем
                continue
            # Собираем массив клемм по данной жиле
            if wire in result:
                result[wire].append(clemm)
            else:
                result[wire] = [clemm]
    
        # Удаляем все жилы с кол-вом клемм меньше 2 (у них нет перемычек)
        remove_items = []
        for wire in result:
            if len(result[wire]) < 2:
                remove_items.append(wire)
        for wire in remove_items:
            result.pop(wire)
    
        return result



# Монтажка для заданного клеммника по возрастанию позиций клемм
#get_montage(b, '06', 'X2')
#
#[{'MKC01-0506/4': ['2', '1']},
# {'MKC01-0624/11': ['4', '3']},
# {'MKC01-0406/2': ['6', '5']},
# {'MKC01-0506/1': ['9', '8']},
# {'MKC01-0608/1': ['11', '10']}]
def get_montage(cabin, clemmnic):
    # Формируем монтажку
    result = []
    if clemmnic not in clemmnic_data.get_cabine(cabin):
        if clemmnic not in clemmnic_data.get_list_terminals(cabin, check_cabel_present=False):
            raise Exception(cabin, clemmnic, f"Клеммника {clemmnic} в шкафу {cabin} нет!")
        else:
            return result

    X = clemmnic_data.get_cabine(cabin)[clemmnic]
    cables = {}
    for terminal in X.keys():
        for wire in X[terminal].keys():
            for cable in X[terminal][wire]:
                if cable_skip_added_to_montage(cabin, cable):
                    continue
                if cable not in cables.keys():
                    cables[cable] = []
                cables[cable].append(terminal)
    # Сортируем монтажку по возврастанию клемм
    check = {}
    for _ in cables.keys():
        Min = 100000
        for cable in cables.keys():
            if cable in check.keys():
                continue
            for pin in cables[cable]:
                if station.get_number(pin, cabin, clemmnic) < Min:
                    Min = station.get_number(pin, cabin, clemmnic)
                    cable_min = cable
        check[cable_min] = 1
        result.append({cable_min: cables[cable_min]})
    return result


# Не добавлять в тонтажу для данного шкафа кабеля
def cable_skip_added_to_montage(cabin, cable):
    result = False
    excluded_cable = station.get_excluded_cable()
    for full_direction in excluded_cable:
        checked_cabine, checked_cable = get_cable_by_direction(full_direction).split(':')
        if cabin == checked_cabine and cable == checked_cable:
         result = True
    return result


# Magic constant:
# 50 - width table (20 + 10 + 20)
# 10 - length between wires in different cable
# 4 - height one row
AA = {'ШИРИНА': 999999, 'ВЫСОТА': 999999, 'КЛЕММ НА ЛИСТЕ': 99999}
A3 = {'ШИРИНА': 420-40, 'ВЫСОТА': 297-10, 'КЛЕММ НА ЛИСТЕ': 70} # 70 ~ ((420-40) - 100)/4, 100 - подпись кабелей, 4 высота ячейки
A2 = {'ШИРИНА': 594-40, 'ВЫСОТА': 420-10, 'КЛЕММ НА ЛИСТЕ': 110}
A4 = {'ШИРИНА': 297-40, 'ВЫСОТА': 210-10, 'КЛЕММ НА ЛИСТЕ': 40}


# Формируем монтажные ячейки (целый или часть клеммника который поместится на лист заданного формата
def calc_montage_data(cabins, frame=A3, check_cabel_present=True):
    count_clemms_in_cheet = frame['КЛЕММ НА ЛИСТЕ']
    result = {}

    not_process_cabins = station.get_excluded_closet()
    for cabin in cabins:
        if cabin in not_process_cabins:
            continue
        result[cabin] = []
        
        for clemmnic in clemmnic_data.get_list_terminals(cabin, check_cabel_present):
            def get_real_clemmnics(cabin, clemmnic):
                result = [clemmnic]
                data = station.get_real_clemmnic()
                if cabin in data and clemmnic in data[cabin]:
                    result = data[cabin][clemmnic]
                return result

            def init_x():
                result = {}
                for real_clemmnic in get_real_clemmnics(cabin, clemmnic):
                    for clemma, wires in clemmnic_data.get_clemnic(cabin, real_clemmnic).items():
                        def check_clemma(clemma, X):
                            if clemma in X:
                                raise TerminalIsBusy(f'Клемма {clemmnic}:{clemma} в шкафу {cabin} уже занята жилой {X[clemma]}, а ты пытаешься туду добавить {wires}!')
                        check_clemma(clemma, result)
                        result[clemma] = wires
                return result

            def init_y():
                result = []
                for real_clemmnic in get_real_clemmnics(cabin, clemmnic):
                    for y in get_montage(cabin, real_clemmnic):
                        cable = get_cable(y)
                        def check_cable(cable, Y):
                            for _y in Y:
                                added_cable = get_cable(_y)
                                if cable == added_cable:
                                    raise CableIsBusy(f'Кабель {cable} уже сидит на клеммах {_y[cable]}, а ты пытаешься его подсадить на {y[cable]}!')
                        check_cable(cable, result)
                        result.append(y)
                return result

            X = init_x()
            Y = init_y()

            first, last = first_and_last_plus_1(X, cabin, clemmnic)
            while True:
                multi_table = False
                if last - first > count_clemms_in_cheet:
                    last = first + count_clemms_in_cheet
                    multi_table = True

                Y_shrink = get_montage_in_range(Y, first, last, cabin, clemmnic)

                # X содержин весь клеммник, так как необходим для отрисовки перемычек
                # Y_shrink содержить нужную часть кабелей для подключения
                # first, last содержать интервал млеммника X который будет отрисовываться в монтажной ячейка
                # ToDo переделать X оставив только необходимы интервал, а перемычки пусть сроятся по аналогии с Y_shrink
                result[cabin].append(MontageCell(cabin, clemmnic, X, Y_shrink, first, last))
                
                if multi_table == True:
                    first = last
                    _, last = first_and_last_plus_1(X, cabin, clemmnic)
                else:
                    break
    return result

def add_cell_to_page_contens(cell, contents, current_page):
    title_long = get_long_cabinet_name(station, int(cell.cabin))
    # Составляем оглавление монтажек
    page_for_contents = current_page + 1
    if title_long not in contents:
        contents[title_long] = [page_for_contents]
    else:
        search_page_result = False
        for i in contents[title_long]:
            if i == page_for_contents:
                search_page_result = True # Пропускаем страницы которые уже присутствуют в оглавлении монтажек
                break
        if search_page_result == False: # Если монтажка у шкафа перенесена на новую страницы, то запоминаем ее
            contents[title_long].append(page_for_contents)


class Possition():
    def __init__(self, frame):
        self._frame = frame
        self._start_x = self._frame['ВЫСОТА']
        self._height_spds_frame = 25  # 25 - высота штампа надписи посл. листов СПДС
        self._begin_x = self._start_x + self._height_spds_frame
        self._begin_y = self._frame['ШИРИНА']
        self._offset_y = self._begin_y
        self._max_width_x = 0
        self._page_number = 1

    def _shift_x_to_next_page(self):
        self._begin_x = self._start_x + self._frame['ВЫСОТА']*self._page_number + self._height_spds_frame
        self._page_number = self._page_number + 1

    # Вылезли за края формата по оси Х
    def _move_outside(self, width_x):
        return self._begin_x + width_x > self._start_x + self._frame['ВЫСОТА']*self._page_number

    def cell_possition(self, cell):
        width_x, height_y = cell.get_size()
        # Выщитываем координаты для печати монтажки
        end_montage_y = self._offset_y - height_y
        if end_montage_y < 0:  # Вылезли за края формата по оси У
            self._begin_x = self._begin_x + self._max_width_x
            if self._move_outside(width_x):  # Вылезли за края формата по оси Х
                self._shift_x_to_next_page()
            self._max_width_x = width_x
            self._offset_y = self._begin_y
        elif self._move_outside(width_x):  # Вылезли за края формата по оси Х, но по Y пока вписываемся
            self._shift_x_to_next_page()
            self._max_width_x = width_x
            self._offset_y = self._begin_y
        
        if width_x > self._max_width_x:
            self._max_width_x = width_x

        result_offset_y = self._offset_y
        self._offset_y = self._offset_y - height_y
        
        return self._begin_x, result_offset_y, self._page_number


class MontageCable():
    def __init__(self, frame=A3):
        self._montage_cell = calc_montage_data(clemmnic_data.get_list_cabine(), frame)
        self._frame = frame
        self._contents = {}


    def get_montage(self):
        # Массив с названием кабеля и координатой точки, куда вписать текст страницы
        # для каждого кабеля всегда четное число точек, так как пишем страницы в оба конца.
        cable_in_multiply_cell = {}
        cables_ground = {}
        result = []
        not_process_cabins = station.get_excluded_closet()
        possition = Possition(self._frame)
        
        for cabin, cells_in_cabin in self._montage_cell.items():
            for cell in cells_in_cabin:
                if cell.count_cable() == 0:
                    continue
                try:
                    begin_x, offset_y, page_number = possition.cell_possition(cell)
                    offset_x = begin_x + 10*get_count_cable_in_left_side(cell.Y, cabin)
        
                    add_cell_to_page_contens(cell, self._contents, page_number)
        
                    result += describe_cabin(cell, begin_x, offset_y)
                    result += plot_border(cell, offset_x, offset_y)
                    result += plot_table(cell, offset_x, offset_y)
                    result += plot_jumper(cell, offset_x, offset_y)
                    result += plot_wires(cell, cells_in_cabin, offset_x, offset_y, cables_ground, cable_in_multiply_cell)
                except Exception:
                    print(cell)
                    raise
    
        result += plot_sheet_with_same_cable(self._frame['ВЫСОТА'], cable_in_multiply_cell)
        return result

    def get_contents(self):
        result = {}
        for cabin in self._contents:
            if len(self._contents[cabin]) == 1:
                result[cabin] = str(self._contents[cabin][0])
            else:
                result[cabin] = str(self._contents[cabin][0]) + ' - ' + str(self._contents[cabin][-1])
        return result


def get_wire_and_device(cell, clemma):
    wire_outside = ""
    device_inside = ""
    if clemma in cell.X.keys() and len(clemma) > 0:
        wire_outside = cell.X[clemma][0]
        wire_inside = cell.X[clemma][1]
        device_inside = contact_data.get_device(cell.cabin, wire_inside)
    return (wire_outside, device_inside)


def get_cable_left_and_right(cell, clemma):
    cable_left = ""
    cable_right = ""
    for y in cell.Y:
        cable = get_cable(y)
        if clemma in y[cable]:
            if in_right_side(cable, cell.cabin):
                if cable_right != "":
                    cable_right += ", "
                cable_right += cable
            else:
                if cable_left != "":
                    cable_left += ", "
                cable_left += cable
    return cable_left, cable_right


def get_jumper_possition(cell, clemma):
    jumper_possition = ""
    for i, (_, clemms) in enumerate(cell.get_jumped_wires().items(), start=1):
        if station.get_number(clemma, cell.cabin, cell.clemmnic) in clemms:
            jumper_possition = i
            break
    return jumper_possition


def montage_scheme_array():
    result = []
    for _, cells_cabin in calc_montage_data(clemmnic_data.get_list_cabine(), frame=AA).items():
        for cell in cells_cabin:
            for i in range(cell.count_clemms()):
                clemma = station.get_clemma(cell.first+i, cell.cabin, cell.clemmnic)
                wire_outside, device_inside = get_wire_and_device(cell, clemma)
                cable_left, cable_right = get_cable_left_and_right(cell, clemma)
                jumper_possition = get_jumper_possition(cell, clemma)

                a = {}
                a["Кабель слева"] = cable_left if cable_left else ""
                a["Перемычка слева"] = jumper_possition if is_left_jumper(cell) else ""
                a["Жила"] = wire_outside
                a["Шкаф"] = cell.cabin
                a["Клеммник"] = cell.clemmnic
                a["Клемма"] = clemma
                a["Устройство"] = device_inside
                a["Перемычка справа"] = jumper_possition if not is_left_jumper(cell) else ""
                a["Кабель справа"] = cable_right if cable_right else ""
                result.append(a)
    return result


# ToDo Вынести в подмодуль, Формирование файлы для печати бирок на кабель
def _cables_in_clemma(cell, clemma):
    result = []
    for y in cell.Y:
        cable = get_cable(y)
        if clemma in y[cable]:
            result.append(cable)
    return result
    
def _insert_reserve(mark_cores):
    result = []
    corrent_cable = None
    for core in mark_cores:
        if corrent_cable is not None:
            if corrent_cable != core["Кабель"]:
                a = {}
                a["Кабель"] = corrent_cable
                a["Жила"] = "Резерв"
                a["Клеммник"] = ''
                result.append(a)
        result.append(core)
        corrent_cable = core["Кабель"]
    if corrent_cable is not None:
        result.append({"Кабель": corrent_cable, "Жила": "Резерв", "Клеммник": ""})
    return result

def _format_output(mark_cores):
    result = defaultdict(list)
    for cabine, cores in mark_cores.items():
        for core in cores:
            cabine_name = station.get_cabine_name(cabine).short
            result[cabine_name].append({cabine_name: f'{core["Кабель"]}  {core["Жила"]}  {core["Клеммник"]}'})
    return result

def _mark_cores_in_cabin(cells_cabin, mm1, mm2):
    result = []
    for cell in cells_cabin:
        for i in range(cell.count_clemms()):
            clemma = station.get_clemma(cell.first+i, cell.cabin, cell.clemmnic)
            wire_outside, _ = get_wire_and_device(cell, clemma)
            cables = _cables_in_clemma(cell, clemma)
            for cable in cables:
                section = None
                if station.preset_cables().exist(cable):
                    section = station.preset_cables().get_gauge(cable)
                elif cables_collection.cable_exist(cable):
                    section = cables_collection.section(cable)[0]
                else:
                    raise(Exception(cable, 'Запрос сечения кабеля, которые не определен ни в PresetCables ни в CablesCollection!'))

                if mm1 <= float(section) < mm2:
                    a = {}
                    a["Кабель"] = cable
                    a["Жила"] = wire_outside
                    a["Клеммник"] = f'{cell.clemmnic}:{clemma}'
                    result.append(a)
    return _insert_reserve(sorted(result, key=lambda x: x['Кабель']))

def mark_cores(mm1, mm2):
    result = {}
    for cabine, cells_cabin in calc_montage_data(clemmnic_data.get_list_cabine(), frame=AA).items():
        result[cabine] = _mark_cores_in_cabin(cells_cabin, mm1, mm2)
    return _format_output(result)

def output_clemmnics(mm1, mm2, output_file_name):
    import pandas
    with safe_excel_writer(output_file_name) as writer:
        for cabine, cores in mark_cores(mm1, mm2).items():
            df = pandas.DataFrame(cores)
            if df.empty:
                continue
            df.to_excel(writer, sheet_name=cabine, index=False)