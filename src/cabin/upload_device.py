import pandas
from collections import Counter
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)
pandas.options.display.expand_frame_repr = False

from sys import stderr

from src.station import config
from src.misc import isNaN
from src.misc import file_exist


Point = namedtuple('Point', 'x y')
ContactBlock = namedtuple('Contact', 'number direction point x y')
DeviceBlock = namedtuple('Device', 'point x y info count row man art type')
DeviceUnites = namedtuple('Devices', 'visiable hidden offset')

Clemmnic = namedtuple('Clemmnic', 'art device')
Jumper = namedtuple('Jumper', 'first count')

CABIN = None
device_directory = None

start_x = -5000
start_y_dev = 5000
start_y_clem = 5400


def is_float(element):
    #If you expect None to be passed:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


def contact_possition(direction):
    match direction:
        case 'Л': x, y = (5, 1)
        case 'П': x, y = (-5, 1)
        case 'Н': x, y = (0, 3)
        case 'В': x, y = (0, -3)
    return (x, y)


def get_devices(file_name):
    visiable = []
    hidden = []
    offset = 10
    for _, row in pandas.read_excel(file_name, sheet_name='Devices', dtype=str).iterrows():
        if 'Смещение' in row and not isNaN(row['Смещение']) and is_float(row['Смещение']):
            offset = int(float(row['Смещение']))
            
        db = DeviceBlock(
            Point(float(row['Положение X']), float(row['Положение Y'])),
            int(row['Ширина']),
            int(row['Высота']),
            row['Информация'],
            row['Количество'],
            row['Строка'],
            row['Производитель'],
            row['Артикул'],
            row['Тип'],
        )
        logger.debug(f"Из файла настроек устройства прочитано устройство: {db}")
        if int(row['Видимость']) == 1:
            visiable.append(db)
        else:
            hidden.append(db)
    return DeviceUnites(visiable, hidden, offset)


def get_contacts(file_name):
    result = []
    for _, row in pandas.read_excel(file_name, sheet_name='Contacts', dtype=str).iterrows():
        x, y = contact_possition(row['Монтаж'])
        contact = ContactBlock(
            row['Номер'],
            row['Монтаж'], 
            Point(float(row['Положение X']), float(row['Положение Y'])),
            x,
            y
        )
        result.append(contact)
        logger.debug(f"Из файла настроек устройства прочитан контакт: {contact}", )
    return result

def get_width(device):
    vis_x = [i.point.x for i in device.visiable]
    hid_x = [i.point.x for i in device.hidden]
    vis_w = [i.point.x + i.x for i in device.visiable]
    hid_w = [i.point.x + i.x for i in device.hidden]
    return max(vis_w + hid_w) - min(vis_x + hid_x)

def get_height(device):
    vis_y = [i.y for i in device.visiable]
    hid_y = [i.y for i in device.hidden]
    return max(vis_y + hid_y)

def get_major_name(name):
    result = name
    if (pos := name.find('.')) != -1:
        result = name[:pos]
    return result

def insert_device_with_contacts(device_data, skip_device=[]):
    devices = {}
    contacts = {}
    device_articuls = [d.man_art for d in device_data.get_device(CABIN)]
    articuls = sorted(Counter(device_articuls).keys())

    for device_type in articuls:
        file_name = f'{device_directory}/{device_type}.xlsx'
        if file_exist(file_name):
            logger.info(f"Читаем настройки устройства из фуйла: {file_name}")
            contacts[device_type] = get_contacts(file_name)
            devices[device_type] = get_devices(file_name)
        else:
            logger.warning(f"Не определено устройство:[{device_type}] в каталоге {device_directory}. Не существует файла {file_name}")

    x, y = (start_x, start_y_dev)
    result = ''
    
    for device_type in articuls:
        if device_type not in devices:
            continue
        height = get_height(devices[device_type])
        x, y = (start_x, y - max(200, height + 50))
        previous_major_name = ''
        for d in sorted(device_data.get_device(CABIN)):
            if d.man_art != device_type:
                continue
            if d.man_art not in devices and d.man_art not in contacts:
                continue
            if d.man_art in skip_device:
                continue

            major_name = get_major_name(d.device)
            if previous_major_name == major_name:
                x -= devices[device_type].offset  # Нулевой пробел между Блоками одного устройства
            previous_major_name = major_name

            logger.info(f"Обрабатываем устройство: {d}")

            result += get_block_represent(
                contacts[device_type],
                devices[device_type],
                device_type, d, x, y
            )

            width = get_width(devices[device_type])

            result += '(setvar "CLAYER" "Подпись устройств")\n'
            if major_name == d.device:
                result += f'(command "_text" "_MC" \'({x + width/2} {y-10}) 6 0 "{d.device}")\n'
            else:
                # Доп. контакты подписываем на самих блоках
                result += f'(command "_text" "_MC" \'({x + width/2} {y + height/2}) 6 90 "{d.device}")\n'

            x += width + devices[device_type].offset
    return result


def insert_clemmnic_with_contacts(device_data, montage_cable, skip_clemmnic=[]):
    x = start_x
    y = start_y_clem
    result = ''
    for clemmnic in sorted(device_data.get_clemmnics(CABIN)):
        logger.info(f"Построение клеммника: {clemmnic}")
        if clemmnic.device in skip_clemmnic:
            continue
        clemmnic_block = ClemmnicBlock(montage_cable, clemmnic)
        if clemmnic_block.device_units == None or clemmnic_block.list_clemms == None:
            continue
        visiable_size_x = max([v.x for v in clemmnic_block.device_units.visiable])
        visiable_size_y = max([v.y for v in clemmnic_block.device_units.visiable])
        result += get_block_represent(clemmnic_block.list_clemms, clemmnic_block.device_units, '-', clemmnic, x, y)
        result += get_number_represent(clemmnic_block.list_numbers, x, y)
        result += get_name_represent(clemmnic_block, clemmnic.device, visiable_size_x, visiable_size_y, x, y)
        x += (visiable_size_x + 100)
    return result


def lisp_block_device(x, y, device_name, device, type_device):
    lisp = ''
    lisp += f'(InsertBlock \'({x + device.point.x} {y + device.point.y}) '
    lisp += f'{device.x} {device.y} "{device.info}" "{device.count}" "{device_name}" '
    lisp += f'"{device.row}" "{device.man}" "{device.art}" "{type_device}")\n'
    return lisp


def lisp_block_contact(x, y, device_name, contact, type_device):
    lisp = ''
    lisp += f'(InsertContact \'({x + contact.point.x} {y + contact.point.y}) '
    lisp += f'"{device_name}" "{contact.number}" "{contact.direction}" "{type_device}" '
    lisp += f'"{contact.x}" "{contact.y}")\n'
    return lisp


def get_block_represent(contacts, devices, type_device, d, x, y):
    lisp = '(setvar "CLAYER" "Модель")\n'
    for contact in contacts:
        lisp += lisp_block_contact(x, y, d.device, contact, type_device)
    lisp += '(setvar "CLAYER" "Для спецификации")\n'
    for device in devices.hidden:
        lisp += lisp_block_device(x, y, d.device, device, device.type)
    lisp += '(setvar "CLAYER" "1-2")\n'
    for device in devices.visiable:
        lisp += lisp_block_device(x, y, d.device, device, device.type)
    return lisp


def get_number_represent(list_numbers, x, y):
    result = ''
    for i, el in enumerate(list_numbers, start=1):
        result += f'(command "_text" "_MC" \'({x + el[0]} {y + el[1]}) 3 0 "{i}")\n'
    return result

def get_name_represent(clemmnic_block, name, visiable_size_x, visiable_size_y, x, y):
    result = '(setvar "CLAYER" "Подпись устройств")\n'
    logger.info(f'Назначаем имя клеммнику {name=}')
    logger.info(f'Его размеры: x={visiable_size_x} y={visiable_size_y}!')
    logger.info(f'Направление монтажа {clemmnic_block.direction}!')
    if clemmnic_block.direction in ('В', 'Н'):
        result += f'(command "_text" "_MC" \'({x + visiable_size_x/2} {y-10}) 6 0 "{name}")\n'
    else:  # clemmnic_block.direction in ('Л', 'П')
        result += f'(command "_text" "_MC" \'({x-1} {y + visiable_size_y/2}) 6 0 "{name}")\n'
    return result


class Jumpers:
    def __init__(self, type_jumpers, intersection=True):
        self._a = type_jumpers
        self._intersection = intersection
        self._ostatok = 1 if intersection else 0
        self._cache = []

    def _my_sum(self, l):
        if self._intersection == False:
            result = sum(l)
        else:
            result = sum(l) - len(l) + 1
        return result

    def _get_key(self, i):
        result = None
        for k, v in self._a.items():
            if i == v:
                result = k
                break
        return result

    def _answer(self, jumpers, num):
        result_type = []
        for j in jumpers:
            result_type.append(self._get_key(j))
        result_count = []
        for j in jumpers:
            result_count.append(j)
        else:
            result_count[-1] -= self._my_sum(jumpers) - num
        return (result_type, result_count)

    def _grate(self, num, l, count):
        return num > self._my_sum(l) + count - self._ostatok
    
    def __call__(self, num):
        result = []
        
        while self._my_sum(result) < num:
            for count in self._a.values():
                if self._grate(num, result, count):
                    continue
                else:
                    result.append(count)
                    break
            else:
                result.append(count)
        return self._answer(result, num)

    @staticmethod
    def get_jumpers(type_jumpers, cabin, montage_cable, clemmnic, intersection = True):
        result = {}
        jumper = Jumpers(type_jumpers, intersection = intersection)
        jumpers = get_near_jumper(cabin, montage_cable, clemmnic)
        if not jumpers:
            return result
        for j in jumpers:
            types, counts = jumper(j.count)
            if len(types) != len(counts):
                raise Exception(cabin, clemmnic, types, counts, """
                    Типов перемычек и самих перемычек должно быть одинаково
                    При использовании одной перемычки более 1 раза эту функцию нужно переписать"""
                )
            start_jumper = j.first
            res = []
            for k in counts:
                res.append(Jumper(start_jumper, k))
                start_jumper += k - 1 if intersection else k
            for i, t in enumerate(types):
                if t not in result:
                    result[t] = []
                result[t].append(res[i])
        
        return result


class ClemmnicBlock:
    def __init__(self, montage_cable, clemmnic):
        self._station = config.get_station()
        self._cabin = config.get_default_cabin()
        self._cabine_definition = self._station.get_cabine_data(self._cabin)
        
        self._montage_cable = montage_cable
        self._clemmnic = clemmnic.device
        self._art = clemmnic.man_art
        
        self.direction = self._cabine_definition.get_clemmnic_direction(self._clemmnic)
        self._count = self._count_clemms(self._montage_cable.clemmnic_data)

        self.device_units = None
        self.list_clemms = None
        self.list_numbers = None
        self._read_clemmnic()


    def _count_clemms(self, clemmnic_data):
        """Возвращает количество клемм в заданном клеммники."""
        result = self._cabine_definition.get_count_clemms(self._clemmnic)
        my_int = lambda x: self._station.get_number(x, self._cabin, self._clemmnic)
        for c in clemmnic_data:
            if c.cabin != self._cabin or c.clemmnic != self._clemmnic:
                continue
            if my_int(c.clemma) > result:
                result = my_int(c.clemma)
        return result
    
    
    def _init_contacts_block(self, clemmnics):
        """Выщитываем и инициализируем контакты, их кол-во и номера"""
    
        result = []
        rows, _ = clemmnics
        for i, row in enumerate(rows, start=1):
            self.direction = row['Монтаж']
            point = Point(
                float(row['Положение X']),
                float(row['Положение Y'])
            )
            x, y = contact_possition(self.direction)
            result.append(
                ContactBlock(i, self.direction, point, x, y)
            )
        return result
    
    
    def _init_contact(self, device):
        """
        Выщитываем и инициализируем контакты, их кол-во и номера.
        Более высокая функция (обвязка над _init_contact)
        """
        
        result = None
        if self.direction in ('В', 'Н'):
            result = self._init_contacts_block(
                config_clemmnic(self._cabin, device.width, device.height, self._count, self.direction)
            )
        else:
            result = self._init_contacts_block(
                config_clemmnic(self._cabin, device.height, device.width, self._count, self.direction)
            )
        return result
    
    
    def _init_clemmnic(self, device):
        """Выщитываем и инициализируем клеммы"""
        
        if self.direction in ('В', 'Н'):
            width = int(device.width * self._count)
            height = int(device.height)
        else:
            width = int(device.height)
            height = int(device.width * self._count)
    
        return DeviceBlock(
            Point(0, 0),
            width,
            height,
            device.info,
            self._count,
            1,
            device.man,
            device.art,
            device.type,
        )
    
    
    def _init_number_contacts(self, device):
        result = []
        if self.direction in ('В', 'Н'):
            y = device.height / 2
            for i in range(self._count):
                result.append((device.width / 2 + i * device.width, y))
        else:
            x = device.height / 2
            for i in range(self._count):
                result.append((x, self._count * device.width - device.width / 2 - i * device.width))
        return result
    
    
    def _init_isolator(self, device, clemmnic_param):
        """Выщитываем и инициализируем торцивой изолятор"""
        
        if self.direction in ('В', 'Н'):
            width = device.width
            height = device.height
            x = clemmnic_param.width * self._count
            y = 0
        else:
            width = device.height
            height = device.width
            x = 0
            y = -1 * device.width
    
        return DeviceBlock(
            Point(x, y),
            width,
            height,
            device.info,
            1,
            0,
            device.man,
            device.art,
            '-',
        )
    
    
    def _init_support(self, device, clemmnic_param):
        """Выщитываем и инициализируем торцивые упоры"""

        if self.direction in ('В', 'Н'):
            width = device.width
            height = device.height
            x = -1 * device.width
            y = (clemmnic_param.height - device.height) / 2
        else:
            width = device.height
            height = device.width
            x = (clemmnic_param.height - device.height) / 2
            y = self._count * clemmnic_param.width
    
        return DeviceBlock(
            Point(x, y),
            width,
            height,
            device.info,
            1,
            0,
            device.man,
            device.art,
            '-',
        )
    
    
    def _init_jumper(self, type_jumpers, clemmnic_param):
        """Выщитываем и инициализируем заводские перемычки"""
        
        result = []

        for jumper_type, jumpers in Jumpers.get_jumpers(type_jumpers, self._cabin, self._montage_cable, self._clemmnic).items():
            for jumper in jumpers:
                length = int(jumper.count * clemmnic_param.width)
                start = clemmnic_param.width * (jumper.first - 1)
                if length == jumper.count * clemmnic_param.width:
                    length -= 1
                    start += 0.5
                if length % 2:
                    length -= 1
                    start += 0.5
    
                if self.direction in ('П', 'Л'):
                    start = self._count * clemmnic_param.width - start - length
                    width = jumper_type.width
                    height = length
                    x = (clemmnic_param.height - jumper_type.width) / 2
                    y = start
                else:
                    width = length
                    height = jumper_type.width
                    x = start
                    y = (clemmnic_param.height - jumper_type.width) / 2
    
                result.append(
                    DeviceBlock(
                        Point(x, y),
                        width,
                        height,
                        jumper_type.info,
                        1,
                        0,
                        jumper_type.man,
                        jumper_type.art,
                        '-',
                    )
                )
        return result
    
    def _read_clemmnic(self):
        """Инициализируем структуры клеммников и контактов, по которым генерируется скрипт lisp."""
        Device = namedtuple('Device', 'man art info type width height')
    
        visiable = []
        hidden = []
        type_jumper = {}
        file_name = f'{device_directory}/{self._art}.xlsx'
        if not file_exist(file_name):
            logger.error(f"Не определен клеммник: {file_name}")
            return (None, None)
        pandas_clemmnic_units = pandas.read_excel(file_name, sheet_name='Devices', dtype=str)
        logger.debug("Краткое содержание файла клеммника:\n%s", pandas_clemmnic_units)

        clemmnic_param = None
        list_clemms = None
        for _, row in pandas_clemmnic_units.iterrows():
            device = Device(
                row['Производитель'],
                row['Артикул'],
                row['Информация'],
                row['Тип'],
                float(row['Ширина']),
                int(float(row['Высота'])),
            )
            if device.type == 'Клемма':
                list_clemms = self._init_contact(device)
                list_numbers = self._init_number_contacts(device)
                visiable.append(
                    self._init_clemmnic(device)
                )
                clemmnic_param = device
            elif device.type == 'Изолятор':
                visiable.append(
                    self._init_isolator(device, clemmnic_param)
                )
            elif device.type == 'Упор':
                visiable.append(
                    self._init_support(device, clemmnic_param)
                )
            elif device.type == 'Перемычка':
                type_jumper[device] = int(row['Контакты'])
                # intersection = int(row['Пересечение'])
                # В случае если перемычки не пересекаются, пока не придумал что делать
    
        if type_jumper:
            if jumpers_device_block := self._init_jumper(type_jumper, clemmnic_param):
                visiable += jumpers_device_block
        offset = 10

        self.device_units = DeviceUnites(visiable, hidden, offset)
        self.list_clemms = list_clemms
        self.list_numbers = list_numbers


def config_clemmnic(cabin, size_x, size_y, total_count, direction):
    result = []
    index = []
    for clemma in range(1, total_count+1):
        match direction:
            case 'Л': x = -14
            case 'П': x = size_x + 14
            case 'В': y = size_y + 14
            case 'Н': y = -14
        a = {}
        a['Монтаж'] = direction
        if direction in ('Л', 'П'):
            a['Положение X'] = x
            a['Положение Y'] = f'{total_count*size_y - size_y/2 - (clemma - 1)*size_y:.1f}'
        else:
            a['Положение X'] = f'{size_x/2 + (clemma - 1)*size_x:.1f}'
            a['Положение Y'] = y
        index.append(clemma)
        result.append(a)
    return (result, index)


def get_count_neighbor_jumper(cabin, montage_cable):
    result_neighbor = {}
    result = {}

    montage_data = montage_cable.calc_montage_data([cabin], montage_cable.AA, check_cabel_present=False)
    
    for data in montage_data[cabin]:
        for wire, clemmnics in data.get_jumped_wires().items():
            if len(clemmnics) == 1 + clemmnics[-1] - clemmnics[0]:
                if data.clemmnic not in result_neighbor:
                    result_neighbor[data.clemmnic] = []
                result_neighbor[data.clemmnic].append(Jumper(clemmnics[0], len(clemmnics)))
            else:
                if data.clemmnic not in result:
                    result[data.clemmnic] = []
                result[data.clemmnic].append(clemmnics)

    return (result_neighbor, result)


def get_near_jumper(cabin, montage_cable, clemmnic):
    result = None
    near, long = get_count_neighbor_jumper(cabin, montage_cable)
    if near and clemmnic in near:
        result = near[clemmnic]
    return result


lisp_main = '''
(defun c:runplot (/)
(vl-load-com)
{}
(setvar "CLAYER" "0")
)

(defun get_block_parameters (vla-getter)
  (vlax-safearray->list (vlax-variant-value (vla-getter (vlax-ename->vla-object (entlast)))))
)

(defun get_block_attributes (/)
  (get_block_parameters vla-GetAttributes)
)

(defun get_block_properties (/)
  (get_block_parameters vla-GetDynamicBlockProperties)
)

(defun change (get_list_data vla-get vla-put key value)
  (foreach item (get_list_data)
    (if (= (vla-get item) key) (vla-put item value)))
)

(defun change_attribute (key value)
  (change get_block_attributes vla-get-TagString vla-put-TextString key value)
)

(defun change_property (key value)
  (change get_block_properties vla-get-PropertyName vla-put-Value key value)
)

(defun make_variant_float (value)
  (vlax-make-variant value 5)
)

(defun make_variant_string (value)
  (vlax-make-variant value 8)
)

(defun InsertBlock (point x y info count name_device row man art type)
  (command "_insert" "БЛОК" point 1 1 0)

  (change_attribute "ИНФОРМАЦИЯ" info)
  (change_attribute "КОЛИЧЕСТВО" count)
  (change_attribute "ИМЯ" name_device)
  (change_attribute "РЯД" row)
  (change_attribute "ПРОИЗВОДИТЕЛЬ" man)
  (change_attribute "АРТИКУЛ" art)
  (change_attribute "ТИП" type)

  (change_property "Ширина" (make_variant_float x))
  (change_property "Высота" (make_variant_float y))
  (change_property "Видимость информации" (make_variant_string "Скрыто"))
)

(defun InsertContact (point name_device number direction type x y)
  (command "_insert" "КОНТАКТ" point 1 1 0)

  (change_attribute "ИМЯ" name_device)
  (change_attribute "НОМЕР" number)
  (change_attribute "МОНТАЖ" direction)
  (change_attribute "ТИП" type)

  (change_property "Положение1 X" (make_variant_float x))
  (change_property "Положение1 Y" (make_variant_float y))
)
'''
