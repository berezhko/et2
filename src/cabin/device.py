from typing import Dict
from collections import defaultdict

from src.misc import file_exist
from src.elements import Text
from .pandas import get_autocad_template_path
from .pandas import make_autocad_template

from . import autocad

from .contact import Contact
from .wire import Wires
from .wire import make_wires

class Device:
    """Класс представляющий Устройство в программе"""
    _connected_wires: Dict = {}
    
    def __init__(self, name):
        self._name = name
        self._contacts = []
        self._plot = [Output(self)]

    def __eq__(self, device):
        return self._name == device._name

    def __str__(self):
        result = self._name + ' >'
        for c in self._contacts:
            result = result + c.contact_name + ' '
        return result

    def _init_contact(self, contact_name: str, wire: str):
        for contact in self._contacts:
            if contact.contact_name == contact_name:
                contact.set_wire(wire)

    def _add_wire(self, device_name: str, contact_name: str, wire: str):
        work_type = self._connected_wires
        if device_name not in work_type:
            work_type[device_name] = {}
        if contact_name in work_type[device_name]:
            print(f"Добавляем в занятую клемму {device_name}:{contact_name} жилу {wire}! А там уже сидит жила: {work_type[device_name][contact_name]}!")
            raise Exception(device_name, contact_name, work_type[device_name], wire, "Добавляем в занятую клемму жилу!")
        work_type[device_name][contact_name] = wire

    def _init_work_type(self, connected_contacts, cabine_definition):
        work_type = self._connected_wires
        for contact in connected_contacts:
            if cabine_definition.is_one_contact_in_wire(contact.wire, contact.device, contact.name):  # Умышленно пропускаем контакты к которым подключена одна жила
                continue
            self._add_wire(contact.device, contact.name, contact.wire)

    def _init_contacts(self, connected_contacts, cabine_definition):
        work_type = self._connected_wires
        if len(work_type) == 0:
            self._init_work_type(connected_contacts, cabine_definition)

        for device_name in work_type:
            if self._name == device_name:
                for contact_name in work_type[device_name]:
                    wire = work_type[device_name][contact_name]
                    self._init_contact(contact_name, wire)

    def used_contacts(self):
        result = []
        for contact in self._contacts:
            if contact.wire() != '':
                result.append(contact)
        return result

    def add_contact(self, contact):
        self._contacts.append(contact)

    def contacts(self):
        return self._contacts

    def contact(self, name):
        result = Contact(0, 0, 0, 0)
        for c in self.contacts():
            if c.contact_name == name:
                result = c
                break
        if result == Contact(0, 0, 0, 0):
            raise Exception(self._name, name, f'Контакт {name} не найден в устройстве {self.name()}! Возможно в сборочном указан контакт с пробельным символом!')
        return result

    def name(self):
        return self._name

    # Гненерируем по внутреннему и внешнему монтажу шкафа список жил и устройства к которым они подключены
    def init_contacts(self, connected_contacts, cabine_definition):
        self._init_contacts(connected_contacts, cabine_definition)

    def _plot_name(self, possition, dx, dy):
        x = possition[0]+dx
        y = possition[1]+dy
        result = [Text((x, y), self.name(), 4, 0, '_MC')]
        return result
        
    def plot_montage_scheme(self, possition):
        result = []
        x, y = possition
        device_name_y_possition = 84
        for p in self._plot:
            result += p.plot_montage_scheme((x, y))
            x += p.get_length()
        result += self._plot_name(possition, self.get_length()/2.0, device_name_y_possition)
        return result

    def get_length(self):
        return sum([p.get_length() for p in self._plot])

    def add_device(self, acad_device):
        self._plot.append(acad_device)

    def get_all_contacts(self):
        result = []
        for p in self._plot:
            result += p.contacts()
        return result

    def is_subdevice(self, device_type):
        result = True
        for p in self._plot:
            if device_type == p.device_type:
                result = False
                break
        return result

class TerminalBlock(Device):
    def __init__(self, device_type, name):
        super().__init__(name)
        self._plot = [autocad.AutocadTerminalBlock(self, device_type)]


class RelaySimple(Device):
    def __init__(self, device_type, name):
        super().__init__(name)
        self._plot = [autocad.AutocadRelaySimple_v2(self, device_type)]


class Unknown(Device):
    def __init__(self, device_type, name):
        super().__init__(name)
        self._plot = [autocad.AutocadUnknown(self, device_type)]


class NGDevice(Device):
    def __init__(self, device_type, name, block):
        super().__init__(name)
        self._plot = [autocad.AutocadBlock(self, device_type, block)]


class Output():
    def __init__(self, device):
        self._device = device

    def _print_contacts(self, contact):
        if contact.wire():
            print(contact, contact.wire(), end=' => ')
            contact.get_back_connection()
            print()
        else:
            print(contact)

    def plot_montage_scheme(self, possition):
        device = self._device
        for c in device.contacts():
            if c.direction != 'Н':
                self._print_contacts(c)
        print()
        for c in device.contacts():
            if c.direction == 'Н':
                self._print_contacts(c)
        print('---')


# Функции конструирования Device
class Devices(Dict[str, Device]):
    def __setitem__(self, key, value) -> None:
        if key in self:
            raise ValueError(f"Дважды создается устройство с одним и тем же именем {key!r}")
        super().__setitem__(key, value)

    def add_contacts(self, contacts):
        for c in contacts:
            if c.device_name not in self:
                raise Exception(c.device_name, c.contact_name, self.keys(), "Устройство не найдено! Возможно оно не преднозначено для конструирования. Проверь его ТИП в схеме, возможно он начинается с '-'.")
            self[c.device_name].add_contact(Contact(c.contact_name, c.device_name, c.center, c.direction))

    def init_back_connection(self, wires):
        for wire in wires.wires().values():
            for edge in wire.pair_contacts():
                u, v = edge
                u.set_back_connection(v)
                v.set_back_connection(u)
                gauge = wire.gauge(u, v)
                u.set_gauge(v, gauge)
                v.set_gauge(u, gauge)

    def init_contacts(self, connected_contacts, cabine_definition):
        for device_name in self:
            device = self[device_name]
            device.init_contacts(connected_contacts, cabine_definition)
    

    def init_contacts_position(self):
        for device in self.values():
            for acad_device in device._plot:
                acad_device.init_contacts_position()

def get_real_device_type(device_type, conf):
    result = device_type
    if 'devices' in conf and device_type in conf.devices:
        result = conf.devices[device_type]
    return result


def is_autocad_block_define(device_type, conf):
    real_device_type = get_real_device_type(device_type, conf)
    return file_exist(get_autocad_template_path(conf.autocad_template_dir, real_device_type))


def load_autocad_block(device_type, autocad_template_dir):
    return make_autocad_template(autocad_template_dir, device_type)


def make_devices(scpecification_unit, conf):
    is_ng_device = {}
    result = Devices()
    for device in scpecification_unit.get_devices():
        real_device_type = get_real_device_type(device.typeplot, conf)
        if device.name not in result:
            if is_autocad_block_define(real_device_type, conf):
                block = load_autocad_block(real_device_type, conf.autocad_template_dir)
                result[device.name] = NGDevice(device.typeplot, device.name, block)
                is_ng_device[device.name] = device.typeplot
            elif real_device_type in ('Промреле Тип1'):
                result[device.name] = RelaySimple(device.typeplot, device.name)
            elif real_device_type in ('Клемма'):
                result[device.name] = TerminalBlock(device.typeplot, device.name)
            else:
                print("Устройство не имеет собственного вида: ", device.typeplot, device.name)
                result[device.name] = Unknown(device.typeplot, device.name)
        elif result[device.name].is_subdevice(device.typeplot):
            if is_autocad_block_define(real_device_type, conf) and device.name in is_ng_device:
                block = load_autocad_block(real_device_type, conf.autocad_template_dir)
                result[device.name].add_device(autocad.AutocadBlock(result[device.name], device.typeplot, block))
                print("Добавление подустойства!", device.name, device.typeplot)
            else:
                raise Exception(
                    device.name, device.typeplot,
                    """
                    Все подустройства и устройство должны иметь собственный блок
                    с контактами в Autocad. Это необходимо для корректного прорисовывания
                    всех контактов самого устройства и его подустройств.
                    """
                )
        else:
            print(device.name, "Дублирование добавление устройство!")
    return result


def construct_devices(G, dil_device, contacts, connected_contacts, cabine_definition):
    devices = make_devices(dil_device, cabine_definition.conf)
    devices.add_contacts(contacts)
    devices.init_contacts(connected_contacts, cabine_definition)
    wires = make_wires(G, devices, connected_contacts, cabine_definition)
    devices.init_back_connection(wires)
    devices.init_contacts_position()
    return devices
