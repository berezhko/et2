from dataclasses import dataclass, field
from typing import Union, List, Tuple, Dict

class Contact:
    """Класс представляющий контакт в пррограмме"""
    def __init__(self, name, device, possition, direction):
        self._name = name
        self._device = device
        self._wire = ''
        self._back_connect = []
        self._possition = possition
        self._direction = direction
        self._section = 0
        self._gauge = {}

    
    @property
    def center(self) -> Tuple[float]:
        return self._possition

    @property
    def full_name(self) -> str:
        return f'{self.device_name}:{self.contact_name}'

    @property
    def device_name(self) -> str:
        return self._device

    @property
    def contact_name(self) -> str:
        return self._name

    @property
    def direction(self) -> str:
        return self._direction

    def available_direction(self):
        return [self.direction]

    def get_coordinate(self, side):
        return self.center

    def s(self, side):
        s = {'Л': ['Низ', 'Верх', 'Центр', 1, lambda x, y: x > y],
             'П': ['Низ', 'Верх', 'Центр', 1, lambda x, y: x < y],
             'Н': ['Лево', 'Право', 'Центр', 0, lambda x, y: x > y],
             'В': ['Лево', 'Право', 'Центр', 0, lambda x, y: x < y]}
        return s[side]


    def __eq__(self, contact):
        return self.contact_name == contact.contact_name and self.device_name == contact.device_name

    def __str__(self):
        return self.full_name

    def __repr__(self):
        return self.full_name

    def __hash__(self):
        return hash(self.full_name)

    def set_back_connection(self, back_connect):
        if back_connect not in self._back_connect:
            self._back_connect.append(back_connect)
            
    def back_connection(self):
        return self._back_connect

    def get_back_connection(self):
        print('(', end='')
        for i, contact in enumerate(self._back_connect):
            if i != 0:
                print(', ', end='')
            print(contact, end='')
        print(')', end='')

    def set_wire(self, wire):
        self._wire = wire

    def wire(self):
        return self._wire

    def contact_connected(self):
        return self.wire() != ''

    def address(self, back_contact):
        address = back_contact.wire() + ' (' + back_contact.full_name + ')'
        if self.direction == 'Н' or self.direction == 'Л':
            address = '(' + back_contact.full_name + ') ' + back_contact.wire()
        return address

    def count_back_connection(self):
        return len(self._back_connect)

    def wire_gauge(self, back_contact):
        return self._gauge[back_contact]

    def set_gauge(self, back_contact, gauge):
        if back_contact not in self._gauge:
            self._gauge[back_contact] = gauge
        else:
            raise Exception(self, back_contact, gauge, self._gauge[back_contact], "Сечение уже назначино для обратного контакта!")

@dataclass(order=True, frozen=True)
class ConnectedContact:
    device: str
    wire: str
    section: float
    name: str
    type: str

    @property
    def full_name(self) -> str:
        return f'{self.device}:{self.name}'
    
    def is_contact_device(self):
        return self.type == 'УСТРОЙСТВО'
    
    def is_contact_clemma(self):
        return self.type == 'КЛЕММНИК'

class ConnectedContactList(List[ConnectedContact]):
    pass