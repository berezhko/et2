from functools import cache
from collections import namedtuple

from .misc import get_short_cabinet_name
from .misc import get_long_cabinet_name
from . import station_settings


class Station:
    def __init__(self, config, Cabine):
        self.conf = config
        self.STATION = config.station
        self.scheme_file = config.scheme_file
        self.cable_set_file = config.cable_set_file
        self.settings_file = config.settings_file
        self.PLOT_DIR = config.plot_dir
        self.OUTPUT_DIR = config.outp_dir
        self.PLACES = config.PLACES
        self.CABEL_PREFIX = config.CABEL_PREFIX
        self.SET_NAME_BY_ORDER = config.SET_NAME_BY_ORDER
        self.START_NUMBER = config.START_NUMBER
        self.CALC_LENGTH = config.CALC_LENGTH
        self.READ_LENGTH_FROM_FILE = config.READ_LENGTH_FROM_FILE
        self.CABINE_FILE = config.CABINE_FILE

        self._Cabine = Cabine
        self._enclosues = station_settings.read_enclosure_list(config)
        self._other_cable = station_settings.read_other_cable(config)
        self._left_jumper = station_settings.read_left_jumper(config)
        self._inner_jumper = station_settings.read_inner_jumper(config)
        self._clemmnics = station_settings.read_clemmnics(config)
        self._inside = station_settings.read_inside_length(config)
        self._outside = station_settings.read_outside_length(config)
        self._real_clemms = station_settings.read_real_clemms(config)
        self._virt_clemms = station_settings.read_virt_clemms(config)
        self._right_cables = station_settings.read_right_cables(config)
        self._excluded_cable = station_settings.read_excluded_cable(config)


    @cache
    def get_cabine_name(self, num):
        Cabine = namedtuple('Cabine', 'short long')
        return Cabine(
            get_short_cabinet_name(self, num),
            get_long_cabinet_name(self, num)
        )

    def get_cabine_data(self, cabine):
        return self._Cabine.make_cabine(cabine, self, self.conf.cabines)

    def get_cabinet_list(self):
        return self._enclosues.get_cabinet_list()

    @cache
    def is_inside(self, num):
        return self._enclosues.is_inside(num, self.conf)

    def is_outside(self, num):
        return not self.is_inside(num)

    # Проверка на то, новый ли шкаф или нет.
    def is_new(self, num):
        return self._enclosues.is_new(num)

    # Виртуальный клеммник, для объединения жил с разных клеммников в один кабель
    def get_virtual_clemmnic(self):
        return self._virt_clemms

    # Виртуальный клеммник, для объединения монтажек в один клеммник
    def get_real_clemmnic(self):
        return self._real_clemms

    def preset_cables(self):
        return self._other_cable
    
    # Шкафы на которые разрабатывается конструкторская документация, по ним не генерируется общая спецификация
    def develop_cabins(self):
        return self._enclosues.develop_cabins()

    # Список шкафов, для которых генерируются данный об устройствах в проекте
    def show_contacts_cabines(self):
        return self._enclosues.show_contacts()

    # Предпочииаемый порядок вывода шкафов в схемах подключения кабелей (по началам кабелей строится заземление кабелей)
    def ordered_cabine(self):
        return self._enclosues.ordered_cabine()

    # Шкафы, которы не нужно печатать в монтажках
    def get_excluded_closet(self):
        return self._enclosues.get_excluded_closet()

    # Шкафы для которых необходимо рассчитать количество и диаметр отверстий под кабель
    def cabine_holes(self):
        return self._enclosues.new_enclosures()

    def distance_inside(self):
        return self._inside

    def distance_outside(self):
        return self._outside

    # Данные кабели и направления в монтажках прорисовываются с правой стороны
    def transit_direction(self):
        return self._right_cables

    # Перемычки, которые на клеммнике прорисоваваются с лево (как правило это цепии ТТ)
    def left_jumper(self):
        return self._left_jumper

    # Кабеля в шкафах, которы не нужно печатать в монтажках
    def get_excluded_cable(self):
        return self._excluded_cable

    # Те шкафы и клеммники в них, перемычки для которых нужно формировать по наименованию внутенних жил
    def select_inner_jumper(self, closet: str, clemnic: str) -> bool:
        return (closet, clemnic) in self._inner_jumper

    # Шкафы, кабельные связи которых будут создавать отдельно 
    def cabine_for_cable_links(self):
        return station_settings.read_cable_links(self.conf)

    # Номера клемм предполагаются числовыми,
    # тут обрабатываем особые случаи из проекта для ТТ и нейтральные клеммы в сборге РТЗО
    @cache
    def get_number(self, clemma, cabine, clemmnic):
        return self._clemmnics.get_number(cabine, clemmnic, clemma)

    # По номеру клеммы, шкафу и клеммнику возвращаем название клеммы
    # Необходимо в раде слчаев, когда клемма имеет не цифровое значение,
    # а ее необходимо поставить в определенное место на клемнике
    @cache
    def get_clemma(self, clemma, cabine, clemmnic):
        return self._clemmnics.get_clemma(cabine, clemmnic, clemma)

    def get_specification(self):
        return station_settings.read_specification(self.conf)

    def test_case(self):
        return self.conf.tests