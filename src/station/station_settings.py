import pandas
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict

from .misc import add_zero


@dataclass(order=True, frozen=True)
class Enclosure:
    number: int
    name: str = field(compare=False)
    long_name: str = field(compare=False)
    building: str = field(compare=False)
    place: str = field(compare=False)
    is_new: bool = field(compare=False)
    order: int = field(compare=False)
    develop_cabins: bool = field(compare=False)
    show_contact: bool = field(compare=False)
    not_montage: bool = field(compare=False)


class EnclosureList(List[Enclosure]):
    def get_enclosure(self, num: int) -> Enclosure:
        result = None
        for c in self:
            if c.number == num:
                result = c
                break
        return result
        
    def get_cabinet_list(self):
        result = {}
        for enclosure in self:
            result[str(enclosure.number)] = [enclosure.name, enclosure.long_name]
        return result

    def is_inside(self, num: int, config):
        result = False
        for enclosure in self:
            if enclosure.number == num and enclosure.place in config.PLACES:
                result = True
                break
        return result

    def is_new(self, num: int):
        result = False
        for enclosure in self:
            if enclosure.number == num:
                result = enclosure.is_new
        return result

    def ordered_cabine(self):
        return [add_zero(cabine.number) for cabine in sorted(self, key=lambda x: x.order) if cabine.order]

    def develop_cabins(self):
        return [add_zero(cabine.number) for cabine in self if cabine.develop_cabins]

    def show_contacts(self):
        return [add_zero(cabine.number) for cabine in self if cabine.show_contact]

    def get_excluded_closet(self):
        return [add_zero(cabine.number) for cabine in self if cabine.not_montage]

    def new_enclosures(self):
        return [add_zero(cabine.number) for cabine in self if cabine.is_new]


@dataclass(frozen=True)
class CableTrait:
    name: str
    number: int
    cabine1: str
    cabine2: str
    type: str
    cores_gauge: str
    length: str
    section: str
    marked: str
    my_part: bool

    @property
    def cores(self):
        return self.cores_gauge.split('x')[0]

    @property
    def gauge(self):
        return self.cores_gauge.split('x')[1]

    @property
    def full_type(self):
        return self.type + ' ' + self.cores_gauge

class PresetCables(Dict[str, CableTrait]):
    # Список кабелей, которые необходимо отобразить в КЖ, с пометкой опреденной в столбце "СУЩЕСТВУЮЩИЙ"
    # Также в монтажках они прописываются с тойже пометкой. При необходимости разбить на 2 функции.
    def get_marked_cables(self):
        result = {}
        for cable, param in self.items():
            if param.marked:
                result[cable] = param.marked
        return result

    # Кабеля которые используются в моем разделе, но добавлял их другой человек.
    # У данных кабелей есть номер, он нужен, чтоб при назначение номеров моим кабелям
    # пропустить уже используемые.
    def get_assigned_cable_in_my_section(self):
        result = []
        for cable, param in self.items():
            if param.my_part:
                result.append(cable)
        return result

    def get_back_cabin(self, cabine_number, cable_name):
        result = -1
        if cable_name in self:
            if self.get_cabine1(cable_name) == cabine_number:
                result = self.get_cabine2(cable_name)
            elif self.get_cabine2(cable_name) == cabine_number:
                result = self.get_cabine1(cable_name)
        return result

    def get_full_type(self, cable_name):
        result = ''
        if cable_name in self:
            result = self.get_cable(cable_name).full_type
        return result

    def exist(self, cable_name):
        return cable_name in self

    def get_cable(self, cable_name):
        result = None
        if cable_name in self:
            result = self[cable_name]
        return result

    def get_notes(self, cable_name):
        return self.get_cable(cable_name).marked

    def get_section(self, cable_name):
        return self.get_cable(cable_name).section
    
    def get_cores_gauge(self, cable_name):
        return self.get_cable(cable_name).cores_gauge
    
    def get_cores(self, cable_name):
        return self.get_cable(cable_name).cores
    
    def get_gauge(self, cable_name):
        return self.get_cable(cable_name).gauge

    def get_type(self, cable_name):
        return self.get_cable(cable_name).type
    
    def get_cabine1(self, cable_name):
        return self.get_cable(cable_name).cabine1
    
    def get_cabine2(self, cable_name):
        return self.get_cable(cable_name).cabine2
    
    def get_length(self, cable_name):
        return self.get_cable(cable_name).length
    
    def directions(self, cable_name):
        return [self.get_cabine1(cable_name), self.get_cabine2(cable_name)]
    
    def number(self, cable_name):
        return self.get_cable(cable_name).number


class Clemmnics:
    def __init__(self):
        self._data = {}

    def init_data(self, df):
        self._data = {}
        for key in df.keys():
            cabines = key[0]
            clemmnic = key[1]
            df_a = df[(cabines, clemmnic, 'A')]
            df_n = df[(cabines, clemmnic, 'N')]
            for cabine in self._get_cabine(str(cabines)):
                s = (add_zero(cabine), clemmnic)
                if s in self._data:
                    continue
                a = []
                for i in df_a:
                    if i:
                        a.append(i)
                n = []
                for i in df_n:
                    if i:
                        n.append(int(i))
                self._data[s] = {"A": dict(zip(a, n)), "N": dict(zip(n, a))}

    def _get_cabine(self, string_cabines):
        result = set()
        for i in string_cabines.split(","):
            cabines = list(map(int, i.split("-")))
            if len(cabines) == 1:
                result.add(add_zero(cabines[0]))
            else:
                for c in range(cabines[0], cabines[-1]+1):
                    result.add(add_zero(c))
        return result

    def get_number(self, cabine, clemmnic, clemma):
        result = 0
        if clemma.isnumeric():
            result = int(clemma)
        elif (cabine, clemmnic) in self._data:
            if clemma in self._data[(cabine, clemmnic)]['A']:
                result = self._data[(cabine, clemmnic)]['A'][clemma]
            else:
                raise Exception(cabine, clemmnic, clemma, self._data[(cabine, '*')]['A'], "Доопредели настройки новой клеммой!")
        elif (cabine, '*') in self._data:
            if clemma in self._data[(cabine, '*')]['A']:
                result = self._data[(cabine, '*')]['A'][clemma]
            else:
                raise Exception(cabine, clemmnic, clemma, self._data[(cabine, '*')]['A'], "Доопредели настройки новой клеммой!")
        else:
            raise Exception(cabine, clemmnic, clemma, "Доопредели настройки новой клеммой!")
        return result

    def get_clemma(self, cabine, clemmnic, clemma):
        result = str(clemma)
        if (cabine, clemmnic) in self._data:
            if clemma in self._data[(cabine, clemmnic)]['N']:
                result = self._data[(cabine, clemmnic)]['N'][clemma]
        elif (cabine, '*') in self._data:
            if clemma in self._data[(cabine, '*')]['N']:
                result = self._data[(cabine, '*')]['N'][clemma]
        return result


def read_enclosure_list(config):
    dtype = {
        'Номер': int,
        'Краткое наименование': str,
        'Полное наименование': str,
        'Здание': str,
        'Помещение': str,
        'Новый': bool,
        'Порядок в монтажках': str,
        'Не добавлять устройства шкафа в спецификацию': bool,
        'Список устройств в листе общих данных': bool,
        'Не печатать в монтажках': bool,
    }

    result = EnclosureList()
    sheet_name = "Шкафы"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name="Шкафы",
            keep_default_na=False,
            dtype=dtype
        )
        for _, row in df.iterrows():
            order = 0
            order_key = "Порядок в монтажках"
            if row[order_key]:
                order = int(row[order_key])
            rows = []
            for key in dtype:
                value = order if key == order_key else row[key]
                rows.append(value)
            enclosure = Enclosure(*rows)
            result.append(enclosure)
    return result


def read_other_cable(config):
    dtype = {
        ("НАПРАВЛЕНИЕ", "Номер"): int,
        ("НАПРАВЛЕНИЕ", "Шкаф1"): str,
        ("НАПРАВЛЕНИЕ", "Шкаф2"): str,
        ("ТИП", "Тип"): str,
        ("ТИП", "Сечение"): str,
        ("ТИП", "Длинна"): str,
        ("ТИП", "Раздел"): str,
        ("СУЩЕСТВУЮЩИЙ", "Пометка для КЖ"): str,
        ("МОЙ РАЗДЕЛ", "Доб. другой сотрудник"): bool,
    }

    result = PresetCables()
    sheet_name = "Прочие кабеля"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            header=[0, 1],
            keep_default_na=False,
            index_col=0,
            dtype=dtype,
        )
        for cable, trait in df.iterrows():
            traits = []
            for key in dtype:
                traits.append(trait[key[0]][key[1]])
            result[cable] = CableTrait(cable, *traits)
    return result


def read_real_clemms(config):
    return _read_clemms(config, "Реальные клеммы")

def read_virt_clemms(config):
    return _read_clemms(config, "Виртуальные клеммы")

def _read_clemms(config, sheet_name):
    result = {}
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            header=[0, 1],
            keep_default_na=False,
            dtype=str,
        )
        result = defaultdict(lambda: defaultdict(list))
        for _, row in df.iterrows():
            for key, value in row.items():
                if value:
                    result[str(key[0])][str(key[1])].append(value)
    return result


def read_inside_length(config):
    return _read_length(config, "Внут дл")

def read_outside_length(config):
    return _read_length(config, "Внеш дл")

def _read_length(config, sheet_name):
    dtype = {
        "Направление": str,
        "Длинна": int
    }
    result = {}
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            keep_default_na=False,
            dtype=dtype,
        )
        for _, row in df.iterrows():
            result[row["Направление"]] = row["Длинна"]
    return result


def read_right_cables(config):
    return _read_cabine_with_cables(config, "Каб Пр")

def read_excluded_cable(config):
    return _read_cabine_with_cables(config, "Каб Не печатаемые")

def _read_cabine_with_cables(config, sheet_name):
    dtype = {
        "Шкаф": str,
        "Кабель": str
    }
    result = []
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            keep_default_na=False,
            dtype=dtype,
        )
        for _, row in df.iterrows():
            result.append(f'{row["Шкаф"]}:{row["Кабель"]}')
    return result


def read_left_jumper(config):
    dtype = {
        "Шкаф": str,
        "Клеммник": str,
        "Жила": str,
    }
    result = []
    sheet_name = "Перем Лв"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            keep_default_na=False,
            dtype=dtype,
        )
        for _, row in df.iterrows():
            result.append(f'{row["Шкаф"]}:{row["Клеммник"]}:{row["Жила"]}')
    return result


def read_inner_jumper(config):
    dtype = {
        "Шкаф": str,
        "Клеммник": str
    }
    result = set()
    sheet_name = "Перем внут"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            keep_default_na=False,
            dtype=dtype,
        )
        for _, row in df.iterrows():
            result.add((row["Шкаф"], row["Клеммник"]))
    return result


def read_cable_links(config):
    result = []
    sheet_name = "Каб связи"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            keep_default_na=False,
            dtype=str,
        )
        for row in df.T.to_numpy():
            a = []
            for cabine in row:
                if cabine:
                    a.append(cabine)
            if a:
                result.append(a)
    return result


def read_clemmnics(config):
    result = Clemmnics()
    sheet_name = "Клеммники"
    if sheet_name in pandas.ExcelFile(config.settings_file).sheet_names:
        df = pandas.read_excel(
            config.settings_file,
            sheet_name=sheet_name,
            header=[0, 1, 2],
            keep_default_na=False,
            dtype=str,
        )
        result.init_data(df)
    return result


# ToDo Добавить проверка на то, есть ли лист 'Спецификация'.
# Также придется менять модуль src.out_connect.specification
def read_specification(config):
    result = pandas.read_excel(
        config.settings_file,
        sheet_name='Спецификация',
        keep_default_na=False
    )
    return result.to_numpy()
