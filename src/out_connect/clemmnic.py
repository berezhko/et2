import pandas
import tabulate

from dataclasses import dataclass, field
from typing import Union, List, Tuple
import logging

logger = logging.getLogger(__name__)

from src.misc import isNaN
from src.exception import EmptyAndNotEmptyClemms
from src.station.misc import get_short_cabinet_name

from .misc import what


@dataclass(order=True)
class Clemmnic():
    cabin: str
    clemmnic: str
    virtual_clemmnic: str = field(compare=False, repr=False)
    real_clemmnic: str = field(compare=False, repr=False)
    clemma: str
    wire: str = field(compare=False)
    inner_wire: str = field(compare=False, repr=False)
    direction: str = field(compare=False)
    number: int = field(compare=False, repr=False)
    cabel: str = field(compare=False)
    type_cabel: str = field(compare=False, repr=False)
    section: Union[str, float] = field(compare=False)
    process: bool = field(compare=False)
    possition: Tuple[float] = field(compare=False, repr=False)
    page: str = field(compare=False)
    


class ClemmnicList(List[Clemmnic]):
    def __init__(self, station):
        self._station = station
    # get_cabine('51')
    # Кл-ки Кл-мы Жилы  Кабеля
    #{'X': {'1': {'1': ['MKC01-1051/1']},
    #       '3': {'3': ['MKC01-1051/1']},
    #       '2': {'2': ['MKC01-1051/1']}}}
    #
    # get_cabine('37')
    #{'X':    { '22': {'KSV3': ['MKC01-2237/1']}, 
    #           '21': {'2200': ['MKC01-2237/1']}},
    # 'UT10': {  '3': {'B122': ['BFE02-1002']},
    #            '2': {'A123': ['BFE02-1002']},
    #           'N5': {'UN12': ['BFE02-1001']},
    #            '1': {'UA12': ['BFE02-1001']},
    #            '4': {'C232': ['BFE02-1002']},
    #          'N10': {'N112': ['MKC01-1037/1']},
    #            '9': {'L112': ['MKC01-1037/1']}},
    # 'UT4': {  'N9': {'XLN1': ['BFE02-1004']},
    #            '8': {'XLB1': ['BFE02-1004']},
    #            '6': {'B123': ['BFE02-1003']},
    #            '5': {'A345': ['BFE02-1003']},
    #            '7': {'C543': ['BFE02-1003']},
    #          'N10': {'N566': ['BFE02-1003']}}}
    def get_cabine(self, cabin):
        result = {}
        for row in self:
            if row.cabin != cabin:
                continue
            if isNaN(row.cabel):
                continue

            if row.clemmnic not in result.keys():
                result[row.clemmnic] = {row.clemma: {row.wire: [row.cabel]}}
                continue
            
            else:
                a = result[row.clemmnic]
                if row.clemma not in a.keys():
                    a[row.clemma] = {row.wire: [row.cabel]}
                else:
                    cable_exist = False
                    # Отладка на случай сбоев с ненайденной жилой в кабеле подключенной к заданной клемме
                    def try_get_list_cable_connected_to_clemm(a, clemmnic, clemma, wire):
                        result = 0
                        try:
                            result = a[clemma][wire]
                        except Exception:
                            raise Exception(f"Не найдена жила {wire} в подготовленной монтажке {a[clemma]} для шкафа {cabin}! Возможная причина: на данную клемму {clemmnic}:{clemma} в другой части схемы уже назначена другая жила (а именно: {a[clemma].keys()})! Проверь схему!")
                        return result

                    for cable in try_get_list_cable_connected_to_clemm(a, row.clemmnic, row.clemma, row.wire):
                        if row.cabel == cable:
                            cable_exist = True
                            break
                    if cable_exist == False:
                        a[row.clemma][row.wire].append(row.cabel)

        return result


    def get_list_terminals(self, cabin, check_cabel_present=True):
        'Выводит список отсортированных список клеммников в шкафу cabin'
        result = []
        for row in self:
            if row.cabin != cabin:
                continue
            if check_cabel_present and isNaN(row.cabel):
                continue
            clemmnic = row.real_clemmnic
            if clemmnic not in result:
                result.append(clemmnic)
        return sorted(result)

    def _get_attribute(self, cabin, name_clemmnic, param):
        result = None
        clemmnic, clemma = name_clemmnic.split(":")
        for i in self:
            if i.cabin == cabin and i.clemmnic == clemmnic and i.clemma == clemma:
                result = what(i, param)
                break
        return result

    def page_clemmnic(self, cabin, name_clemmnic):
        return self._get_attribute(cabin, name_clemmnic, 'page')

    def possition_clemmnic(self, cabin, name_clemmnic):
        return self._get_attribute(cabin, name_clemmnic, 'possition')


    #get_clemnic(b, '06', 'X2')
    #
    #{'4': ['N361', 'N361'],
    # '8': ['A1603', 'A1603'],
    # '3': ['A362', 'A362'],
    # '9': ['C1603', 'C1603'],
    # '7': ['', ''],
    # '11': ['C618', 'C618'],
    # '10': ['A618', 'A618'],
    # '6': ['0451', '0451'],
    # '5': ['B453', 'B453'],
    # '1': ['B351', 'B351'],
    # '2': ['N351', 'N351']}
    def get_clemnic(self, cabin, clemmnic):
        result = {}
        for row in self:
            if row.cabin != cabin:
                continue
            if row.clemmnic != clemmnic:
                continue
            if row.clemma not in result.keys():
                wire = row.wire
                back_wire = row.inner_wire
                if isNaN(wire):
                    wire = ""
                if isNaN(back_wire):
                    back_wire = ""
                result[row.clemma] = [wire, back_wire]
            else:
                pass
        return result


    # Отсортированные список шкафов (сперва выводятся предпочитаемые кабеля)
    def get_list_cabine(self):
        result = {}
        for row in self:
            if row.cabin != '' and row.cabin not in result.keys() and row.cabin not in self._station.ordered_cabine():
                result[row.cabin] = 1
        return [c for l in [self._station.ordered_cabine(), sorted(result)] for c in l]


    def different_wires(self, cabin):
        'Для шкафа cabin печатаем клеммы, у которых различаются внешняя и внутренняя жилы'
        result = []
        for clemma in self:
            if clemma.cabin != cabin:
                continue
            if clemma.wire != clemma.inner_wire:
                result.append({
                    'Шкаф': cabin,
                    'Клеммник': f'{clemma.clemmnic}:{clemma.clemma}',
                    'Внешняя': clemma.wire,
                    'Внутренняя': clemma.inner_wire,
                    'Лист': clemma.page,
                })
        logger.info(
            f'Клеммники с различающимися внешними и внутренними жилами в шкафу {cabin}!\n%s',
            tabulate.tabulate(result, headers="keys")
        )
        return result


# Ищим пересекающуюся проводку в схеме
def check_intersection_clemmnic(clemmnic_data):
    result = {}
    for i, clemma in enumerate(clemmnic_data):
        if isNaN(clemma.wire):
            continue
        for clemma_prev in clemmnic_data[i+1:]:
            if isNaN(clemma.wire):
                continue
            if clemma_prev == clemma and clemma_prev.wire != clemma.wire:
                key = f'{clemma.cabin}:{clemma.clemmnic}:{clemma.clemma}'
                if key not in result:
                    result[key] = set()
                result[key].add(f'{clemma.wire}: л.{clemma.page}')
                result[key].add(f'{clemma_prev.wire}: л.{clemma_prev.page}')
    return result


def get_clemmnics_in_cabine(station, clemmnic_data, cabin_num):
    '''
    Создает список клеммников которые используются в шкафу. Если между
    используемыми клеммами есть неиспользуемые, то они помечаются как '-'
    '''
    result = {}
    except_list = []

    for clemma in clemmnic_data:
        if clemma.cabin != cabin_num:
            continue

        w_ot = clemma.wire
        pos = clemma.page
        cl = clemma.clemma
        box = clemma.real_clemmnic
        
        if box not in result:
            result[box] = []
    
        not_exist = True
        for value in result[box]:
            if cl != value[box]:
                continue
            not_exist = False
            try:
                value['жила'] = value['жила'] + ', ' + w_ot
                value['лист'] = value['лист'] + ', ' + pos
            except TypeError:
                except_list.append((clemma, value))
            
        if not_exist:
            result[box].append({'жила': w_ot, box: cl, 'лист': pos, '': None})

    if except_list:
        raise EmptyAndNotEmptyClemms(except_list)
    
    for box in result.keys():
        my_int = lambda x: station.get_number(x, cabin_num, box)
        my_str = lambda x: station.get_clemma(x, cabin_num, box)
        
        max_clem = my_int(
            sorted(
                result[box], key=lambda x: my_int(x[box])
            )[-1][box]
        )
        for i in range(1, max_clem+1):
            not_exist = True
            for value in result[box]:
                if my_int(value[box]) == i:
                    not_exist = False
                    break
            if not_exist:
                result[box].append({'жила': '-', box: my_str(i), 'лист': '-'})
    return result


def make_pandas_clemmnics(station, clemms, cabin_num):
    '''
    Создает объединенный pandas.DataFrame содержащий все клеммники шкафа cabin_num
    '''

    result = []
    def box_to_int(x): 
        if x[1:].isnumeric():
            result = int(x[1:]) 
        elif x[2:].isnumeric() and x[1] == 'A':
            result = 10+int(x[2:])
        elif x[2:].isnumeric() and x[1] == 'V':
            result = 20+int(x[2:])
        elif x[2:].isnumeric():
            result = 30+int(x[2:])
        else:
            result = 50
        return result

    for box in sorted(clemms.keys(), key=box_to_int):
        my_int = lambda x: station.get_number(x, cabin_num, box)
        result.append(
            pandas.DataFrame(
                sorted(
                    clemms[box], key=lambda x: my_int(x[box])
                )
            )
        )
    return pandas.concat(result, axis=1)


def used_clemms(station, clemmnic_data, file_name):
    with pandas.ExcelWriter(file_name) as writer:
        for cabin_num in clemmnic_data.get_list_cabine():
            cabin_clemms = get_clemmnics_in_cabine(station, clemmnic_data, cabin_num)
            if cabin_clemms:
                cabin_df = make_pandas_clemmnics(station, cabin_clemms, cabin_num)
                cabin = get_short_cabinet_name(station, int(cabin_num))
                cabin_df.to_excel(writer, sheet_name=cabin, index=False)