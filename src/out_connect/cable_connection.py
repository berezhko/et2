import pandas
from dataclasses import dataclass, field
from typing import Union, List

from src.misc import isNaN

from src.exception import NotFoundDirection
from src.exception import CountUsedWiresModeCountWires
from src.exception import WireInCableAlreadyExist
from src.exception import InvalideSectionOrCableType
from src.exception import NotKnowCable

from src.out_connect.direction import get_cabins_by_direction
from src.out_connect.direction import get_back_cabinet_from_direction
from src.out_connect.direction import is_direction
from src.out_connect.direction import first_closet
from src.out_connect.direction import second_closet
from src.out_connect.direction import make_direction

from src.out_connect.cable import is_kvvg
from src.out_connect.cable import is_utp
from src.out_connect.cable import is_vvg
from src.out_connect.cable import get_kvvg
from src.out_connect.cable import get_utp
from src.out_connect.cable import get_vvg

from .length_cable.length import LengthCable


@dataclass(order=True)
class WireUnit():
    direction: str = field(repr=False)
    number: int = field(repr=False)
    wire: str
    cable: str = field(compare=False)
    clemmnic1: str = field(compare=False)
    virt_clemmnic1: str = field(compare=False, repr=False)
    clemmnic2: str = field(compare=False)
    virt_clemmnic2: str = field(compare=False, repr=False)
    section: str = field(compare=False)
    type_cable: str = field(compare=False)

    def get_debug(self):
        return {
            'НАПРАВЛЕНИЕ':  self.direction,
            'ЖИЛА':  self.wire,
            'КЛЕММНИК1':  self.clemmnic1,
            'ВИРТ_КЛЕММНИК1':  self.virt_clemmnic1,
            'КЛЕММНИК2':  self.clemmnic2,
            'ВИРТ_КЛЕММНИК2':  self.virt_clemmnic2,
            'СЕЧЕНИЕ':  self.section,
            'ТИП_КАБЕЛЯ':  self.type_cable,
            'НОМЕР':  self.number,
            'КАБЕЛЬ':  self.cable,
        }


class CableList(List[WireUnit]):
    _cache_cable_to_direction = {}
    _cache_find_cable_by_direction = {}
    
    def cable_to_direction(self, cable):
        if cable in self._cache_cable_to_direction:
            return self._cache_cable_to_direction[cable]

        result = -1
        for wire_unit in self:
            if wire_unit.cable == cable:
                result = wire_unit.direction
                break
        if result == -1:
            raise NotFoundDirection(cable, "По данному кабелю в массиве CableList небыло найдено НАПРАВЛЕНИЕ!")
        self._cache_cable_to_direction[cable] = result
        return result

    # direct = '#0106:XT1:X4'
    def find_cable_by_direction(self, direct):
        if direct in self._cache_find_cable_by_direction:
            return self._cache_find_cable_by_direction[direct]

        result = 0
        direction, clemmnic1, clemmnic2 = direct.split(':')
        for wire_unit in self:
            if (
                wire_unit.direction == direction and
                wire_unit.clemmnic1 == clemmnic1 and
                wire_unit.clemmnic2 == clemmnic2
            ):
                result = wire_unit.cable
                break
        self._cache_find_cable_by_direction[direct] = result
        return result

    def make_cable_location_from_my_section(self):
        result = {}
        for wire_unit in self:
            cable = wire_unit.cable
            result[cable] = get_cabins_by_direction(wire_unit.direction)
        return result

    def get_debug(self):
        result = []
        for wire_unit in sorted(self):            
            result.append(wire_unit.get_debug())
        return result

    def print_wires_in_cable(self, cable):
        for wire_unit in sorted(self):
            if cable == wire_unit.cable:
                print(wire_unit.get_debug())


class CableConnection:
    def __init__(self, scheme_data, station):
        self.station = station
        self._cables = CableList()
        self._cable_wires = {}
        self._cable_section = {}
        self._cable_index = {}
        self._calc_cable_links(scheme_data)
        self._init_cable_wires()
        self._init_cable_section_plus_type()
        self._length_cable = LengthCable(station, self)

    def get_back_cabin_by_cable(self, cabin, cable):
        result = -1
        preset_cables = self.station.preset_cables()
        if preset_cables.exist(cable):
            result = preset_cables.get_back_cabin(cabin, cable)
        else:
            direction = self.cable_to_direction(cable)
            result = get_back_cabinet_from_direction(cabin, direction)
            
        return result

    def cable_to_direction(self, cable):
        return self._cables.cable_to_direction(cable)
    
    def get_cabins_by_cable(self, cable):
        direction = self.cable_to_direction(cable)
        return get_cabins_by_direction(direction)
    
    # direct = '#0106:XT1:X4'
    def find_cable_by_direction(self, direct):
        return self._cables.find_cable_by_direction(direct)

    def make_cable_location_from_my_section(self):
        return self._cables.make_cable_location_from_my_section()
    
    # Формируем кэш {"ШКАФ": ["КАБЕЛЬ1", "КАБЕЛЬ2", "КАБЕЛЬ3", ...]}
    def make_list_cables_in_closet(self, exclude=[]):
        result = {}
        cable_location = self._make_cable_location()
        
        for cab in cable_location:
            closet1 = cable_location[cab][0]
            closet2 = cable_location[cab][1]
            if closet1 in exclude or closet2 in exclude:
                continue
            
            if closet1 in result:
                result[closet1].append(cab)
            else:
                result[closet1] = [cab]
            if closet2 in result:
                result[closet2].append(cab)
            else:
                result[closet2] = [cab]
        return result

    def wires(self, cable):
        return self._cable_wires[cable]

    def count_used_wires(self, cable):
        return len(self._cable_wires[cable])
    
    def count_wires(self, cable) -> str:
        count_used_wires = self.count_used_wires(cable)
        section_cable, type_cable = self.section(cable)
        result = 0
        if is_kvvg(type_cable):
            result = get_kvvg(count_used_wires, section_cable)
        elif is_vvg(type_cable):
            if type_cable.find('3кВ') != -1:
                result = '1'
            else:
                result = get_vvg(count_used_wires, section_cable)
        elif is_utp(type_cable):
            result = get_utp(count_used_wires, section_cable)
        else:
            result = str(count_used_wires)

        if int(result) < count_used_wires:
            raise CountUsedWiresModeCountWires(count_used_wires, result, cable, 'Используемых жил в кабеле больше чем всего жил!')
        return result
    

    def section(self, cable):
        return self._cable_section[cable]

    def cables(self):
        return list(self._cable_wires.keys())

    def cable_exist(self, cable):
        return cable in self._cable_wires

    def distance_inside(self):
        return self._length_cable.distance_inside()

    def distance_outside(self):
        return self._length_cable.distance_outside()

    def debug(self, unixtime):
        output_dir = self.station.OUTPUT_DIR
        debug = self._cables.get_debug()
        pandas.DataFrame(debug).to_csv(f"{output_dir}/Отладка2-{unixtime}.csv", index=False)
        return pandas.DataFrame(debug)

    def print_wires_in_cable(self, cable):
        self._cables.print_wires_in_cable(cable)


    def _calc_cable_links(self, scheme_data):
        index = 1
        preset_cables = self.station.preset_cables()
        for clemma in scheme_data:
            if isNaN(clemma.cabel):
                continue
        
            back_cabinet = self._get_back_cabinet(clemma.cabin, clemma.direction)
            if clemma.direction in preset_cables:
                direction = preset_cables.directions(clemma.direction)
                clemma.direction = make_direction(*direction)

            if clemma.process == 0:
                back_id = self._find_back_possition(scheme_data, clemma, back_cabinet) # False or Possition in scheme_data
                if back_id != False:
                    back_clemma = scheme_data[back_id]
                    if _compare_cabinet(clemma.cabin, back_clemma.cabin):
                        clemma1 = clemma
                        clemma2 = back_clemma
                    else:
                        clemma1 = back_clemma
                        clemma2 = clemma
                    
                    if preset_cables.exist(clemma.cabel):
                        number = 0
                        cable_name = clemma.cabel
                    elif is_direction(clemma.cabel):
                        number = self._assign_number_of_cable(
                            clemma.direction,
                            clemma1.virtual_clemmnic,
                            clemma2.virtual_clemmnic
                        )
                        cable_name = self._make_cable_name(clemma.cabel, number)
                        
                        self._cables.append(
                            WireUnit(
                                clemma.direction,
                                number,
                                clemma.wire,
                                cable_name,
                                clemma1.clemmnic,
                                clemma1.virtual_clemmnic,
                                clemma2.clemmnic,
                                clemma2.virtual_clemmnic,
                                clemma.section,
                                clemma.type_cabel,
                            )
                        )
                    else:
                        raise NotKnowCable(clemma.cabel, "Неизвестный кабель, проверте схему и массив известных кабелей из других разделов")

                    clemma.process = index
                    back_clemma.process = index
        
                    clemma.cabel = cable_name
                    back_clemma.cabel = cable_name
                    
                    clemma.number = number
                    back_clemma.number = number
                    
                    index = index + 1

    def _init_cable_wires(self):        
        for wire_unit in sorted(self._cables):
            if wire_unit.cable not in self._cable_wires.keys():
                self._cable_wires[wire_unit.cable] = []
            # Проверка на существование жилы
            if wire_unit.wire in self._cable_wires[wire_unit.cable]:
                self._cables.print_wires_in_cable(wire_unit.cable)
                raise WireInCableAlreadyExist(
                    wire_unit.wire,
                    wire_unit.cable,
                    wire_unit.get_debug()
                )
            self._cable_wires[wire_unit.cable].append(wire_unit.wire)

    def _init_cable_section_plus_type(self): 
        for wire_unit in sorted(self._cables):
            # Проверка на единственность сечения и типа кабеля для вех жил в кабеле
            section_plus_type = (wire_unit.section, wire_unit.type_cable)
            if wire_unit.cable not in self._cable_section.keys():
                self._cable_section[wire_unit.cable] = section_plus_type
            elif section_plus_type != self._cable_section[wire_unit.cable]:
                self._cables.print_wires_in_cable(wire_unit.cable)
                raise InvalideSectionOrCableType(
                    wire_unit.cable, wire_unit.wire,
                    section_plus_type,
                    self._cable_section[wire_unit.cable],
                    'В кабель добавляются жилы с другим сечением или типом кабеля!'
                )

    # По шкафу и кабелю возвращаем обратный шкаф, независимо от тогда 'НАШ' или 'НЕ НАШ' кабель.
    def _get_back_cabinet(self, cabin, direction):
        back_cabin = -1
        preset_cables = self.station.preset_cables()
        if is_direction(direction):
            back_cabin = get_back_cabinet_from_direction(cabin, direction)
        if back_cabin == -1:
            cable = direction
            back_cabin = preset_cables.get_back_cabin(cabin, cable)
        return back_cabin

    def _make_cable_name(self, direction, num):
        result = ''
        cable_name = self.station.CABEL_PREFIX + first_closet(direction) + second_closet(direction)
        if num != 0:
            cable_name = cable_name + '/' + str(num)

        if cable_name not in self._cable_index:
            if self.station.SET_NAME_BY_ORDER:
                self._cable_index[cable_name] = self.station.CABEL_PREFIX + str(self.station.START_NUMBER + len(self._cable_index))
            else:
                self._cable_index[cable_name] = cable_name
            
        result = self._cable_index[cable_name]
        return result
    
    # Формируем кэш {"КАБЕЛЬ": ["ШКАФ1", "ШКАФ2"]}
    def _make_cable_location(self):
        result = self.make_cable_location_from_my_section()  # Берем все кабеля нашего раздела
        preset_cables = self.station.preset_cables()  # А также из дрегих разделов,
        for cable_name in preset_cables.get_marked_cables():  # но только те, которые имеют отмеку
            result[cable_name] = preset_cables.directions(cable_name)
        return result


    def _is_number_used(self, number, direction):
        '''
        Проверяем занят ли нормер уже кабелями из моего раздела.
        Кабеля мог назначить другой проектировщик, и выдать мне список
        используемых им кабелей. Либо я их назначил сам (например
        зарезервировал номера (и соответственно именя) для определенных
        направлений, возможно проект уже был выдан и утвержден, и менять
        КЖ и монтажки уже не получится).
        '''
        preset_cables = self.station.preset_cables()
        result = False
        for cable_name in preset_cables.get_assigned_cable_in_my_section():
            direction_preset = preset_cables.directions(cable_name)
            if direction == make_direction(*direction_preset):
                cable_number = preset_cables.number(cable_name)
                if number == cable_number:
                    result = True
                    break
        return result
    
    
    # Назначаем номер для кабеля, либо равные номеру второго конца, 
    # либо слудующий свободные номер (в случае если жила между клеммникапи первая в кабеле)
    def _assign_number_of_cable(self, direction, clemmnic1, clemmnic2):
        number = 0  # Начинаем искать свободный номер кабеля с 0
        for wire_unit in self._cables:
            if wire_unit.direction == direction:
                if wire_unit.number > number:
                    number = wire_unit.number
                if (
                    wire_unit.virt_clemmnic1 == clemmnic1 and
                    wire_unit.virt_clemmnic2 == clemmnic2
                ): # Если нашли противоположный конец в кабеле, то назначить номер этого кабеля
                    return wire_unit.number
        result = number + 1  # После перебора всех кабелей из Шкафа1 в Шкаф2 назначаем следующий свободный номер (противоположный конец пока не назначался)
        while self._is_number_used(result, direction):
            result += 1  # Проверяем наш номер на уже назначенные в проекте кабеля
        return result

    # По ЖИЛА, ШКАФ, КАБЕЛЬ и СЕЧЕНИЕ находим номер второго конца жилы (parse == 0) 
    def _find_back_possition(self, scheme_data, my_own_clemma, back_cabin):
        result = False
        for i, clemma in enumerate(scheme_data):
            if (
                clemma.process == 0 and 
                clemma.wire == my_own_clemma.wire and 
                clemma.cabin == back_cabin and 
                clemma.cabel == my_own_clemma.cabel and 
                clemma.section == my_own_clemma.section and 
                clemma.type_cabel == my_own_clemma.type_cabel
            ):
                if clemma.cabin == my_own_clemma.cabin and clemma.clemmnic == my_own_clemma.clemmnic:
                    continue
                result = i
                break
        return result


def make_cable_connection(clemmnic_data, station):
    return CableConnection(clemmnic_data, station)


# Сравнение порядка шкафов в названии кабеля
def _compare_cabinet(cab, back_cab):
    if int(cab) < int(back_cab):
        return True
    else:
        return False
