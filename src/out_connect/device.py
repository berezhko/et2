from dataclasses import dataclass, field
from typing import Union, List, Tuple

from src.misc import isNaN
from src.edge import calc_distance


@dataclass(order=True, frozen=True)
class Device():
    cabin: str = field(repr=False)
    device: str
    art: str
    order_num: str
    manuf: str
    possition: Tuple[float] = field(compare=False, repr=False)
    page: str = field(compare=False)
    type_view: str = field(compare=False)
    info: str = field(compare=False)
    in_spec: bool = field(compare=False, repr=False)

    @property
    def unit(self):
        result = 'шт.'
        if self.is_cable():
            result = 'м.'
        return result
    
    @property
    def count(self) -> int:
        result = 1
        if self.is_cable():  # У кабеля длинна указывается в поле УСТРОЙСТВО
            result = int(float(self.device)+0.5)
        return result

    @property
    def man_art(self):
        return f'{self.manuf} {self.art}'

    @property
    def full_info(self):
        suffix = ''
        # Если код заказа пустой, то art попадет в код заказа
        # и в информации об устройстве попасть не должен, иначе
        # он будет дважды указан в спецификации
        if self.order_num != '':
            suffix = f' {self.art}'
        return f'{self.info}{suffix}'

    @property
    def true_art(self):
        # Если код заказа пустой, то art будет кодом заказа
        return self.order_num if self.order_num else self.art

    def is_material(self):
        return self.type_view == 'Материал'

    def is_clemmnic(self):
        return self.type_view == 'Клеммник'
    
    def is_cable(self):
        return self.type_view == 'Кабель'

    def is_contact_relay(self):
        return self.type_view in ('НЗ', 'НО', 'НЗ ЗС', 'НО ЗС', 'НЗ ЗВ', 'НО ЗВ', 'НЗО', 'НОЗ')

    def contact_near(self, contact_possition):
        near = self._get_near()
        return near(self.possition, contact_possition)

    def _get_near(self):
        match self.type_view:
            case 'НО':
                return _near_nco
            case 'НЗ':
                return _near_nco
            case 'НО ЗС':
                return _near_nco
            case 'НЗ ЗС':
                return _near_nco
            case 'НО ЗВ':
                return _near_nco
            case 'НЗ ЗВ':
                return _near_nco
            case 'Блокконтакт НО':
                return _near_nco
            case 'Блокконтакт НЗ':
                return _near_nco
            case 'Катушка':
                return _near_nco
            case 'Катушка ДП':
                return _near_dp
            case 'Автомат':
                return _near_nco
            case 'Автомат 2P':
                return _near_2p
            case 'Автомат 3P':
                return _near_3p
            case 'Разъединитель':
                return _near_nco
            case 'Разъединитель 2P':
                return _near_2p
            case 'Разъединитель 3P':
                return _near_3p
            case 'Резистор':
                return _is_near
            case _:
                return _always_near


class DeviceList(List[Device]):
    def get_arts(self, cabin):
        result = set()
        for d in self:
            if d.cabin == cabin:
                result.add(d.art)
        return result

    def get_all_device(self, cabin):
        result = set()
        for d in self:
            if d.cabin == cabin:
                result.add(d)
        return result

    def get_device(self, cabin):
        result = set()
        for d in self.get_all_device(cabin):
            if not d.is_clemmnic():
                result.add(d)
        return result

    def get_clemmnics(self, cabin):
        result = set()
        for d in self.get_all_device(cabin):
            if d.is_clemmnic():
                result.add(d)
        return result

    def get_device_for_spec(self, cabin):
        result = []
        for d in self:
            if d.cabin == cabin and d.in_spec and not d.is_contact_relay():
                result.append(d)
        return sorted(result)


def make_device(row):
    def _get_value(key, values):
        return values[key] if key in values and not isNaN(values[key]) else ''
    return (
        row['ШКАФ'],
        row['УСТРОЙСТВО'],
        row['ТИП'],
        _get_value('АРТИКУЛ', row),
        _get_value('ПРОИЗВОДИТЕЛЬ', row),
        (row['Положение X'], row['Положение Y']),
        row['ЛИСТ'],
        row['Тип1'],
        row['ПРИМЕЧАНИЕ'],
        row['Слой'] != 'Не учитывать в спецификации'
    )


def check_device(devices):
    bad_device = []
    for d in devices:
        if d.in_spec and not d.art:
            bad_device.append(d)
    if bad_device:
        print('Устройство попадет в спецификацию, но у него не указан артикул (ТИП)!')
        print_bad_values(bad_device)


def print_bad_values(array):
    for el in array:
        print(el)
        

def make_device_list(df, station):
    from src.out_connect.pandas import make_device_list
    df = make_device_list(df, station).fillna('')
    result = DeviceList()
    error_devices = []
    for index, row in df.iterrows():
        if row['Тип1'] == "Настройка":
            error_devices.append(make_device(row))
        device = Device(*make_device(row))
        result.append(device)
    if error_devices:
        print_bad_values(error_devices)
        raise Exception("Не настроен тип отображения устройства! Проверь схему!")
    check_device(result)
    return result


class ViewDevice:
    def __init__(self, contact_data, device_data, closet):
        self._contact_data = contact_data
        self._device_data = device_data
        self._closet = closet
        self._showes_contacts = set()

    @classmethod
    def pandas_table(cls, v1, v2, v3, v4, v5, v6, v7):
        result = {}
        result['УСТР.'] = v1
        result['АРТИКУЛ'] = v2
        result['ПРИМЕЧАНИЕ'] = v3
        result['ТИП'] = v4
        result['ЛИСТ'] = v5
        result['КОНТАКТЫ'] = v6
        result['ЖИЛЫ'] = v7
        return result
    
    def _string_elements(self, elements: list):
        result = ''
        for i, el in enumerate(elements):
            if i:
                result += f', {el}'
            else:
                result += el
        return result
    
    def __call__(self, device):
        result = []
        all_contacts = self._contact_data.get_list_contact_in_device(self._closet, device)
        used_contacts = []
        
        for d in self._device_data:
            # Пропускаем все устройства, которые не имеют контактов
            if d.is_material() or d.is_clemmnic() or d.is_cable():
                continue

            if d.cabin == self._closet and d.device == device:
                contacts = []
                wires = []
                for c in all_contacts:
                    if d.contact_near(c.possition):
                        contacts.append(c.clemma)
                        wires.append(c.inner_wire)
                        used_contacts.append(c)

                device_info = (device, tuple(contacts))
                if device_info in self._showes_contacts:
                    continue
                self._showes_contacts.add(device_info)
                result.append(
                    self.pandas_table(
                        d.device,
                        d.art,
                        d.info,
                        d.type_view,
                        d.page,
                        self._string_elements(contacts),
                        self._string_elements(wires)
                    )
                )
    
        contacts = []
        wires = []
        pages = []
        for c in all_contacts:
            if c not in used_contacts:
                contacts.append(c.clemma)
                wires.append(c.inner_wire)
                pages.append(c.page)
        if contacts:
            result.append(
                self.pandas_table(
                    device,
                    '',
                    'Остальные контакты!',
                    '',
                    self._string_elements(pages),
                    self._string_elements(contacts),
                    self._string_elements(wires)
                )
            )
        return sorted(result, key=lambda x: x['АРТИКУЛ'] + x['ТИП'] + x['КОНТАКТЫ'])


def _less_x(a, b):
    return a[0] < b[0]

def _less_y(a, b):
    return a[1] < b[1]

def _is_near(p1, p2, eps=15) -> bool:
    return calc_distance(p1, p2) < eps

def _near_nco(a, b):
    return _near_x(a, b, 15) and _near_y(a, b, eps=0.15) and _less_x(a, b)

def _near_dp(a, b):
    return _near_x(a, b, 22) and _near_y(a, b, eps=11)

def _near_2p(a, b):
    return _near_x(a, b, 11) and _near_y(a, b, eps=16)

def _near_3p(a, b):
    return _near_x(a, b, 11) and _near_y(a, b, eps=32)

def _near_x(a, b, eps=15):
    return _is_near((a[0], 0), (b[0], 0), eps)

def _near_y(a, b, eps=15):
    return _is_near((0, a[1]), (0, b[1]), eps)

def _always_near(a, b):
    return True