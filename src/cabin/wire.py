import copy

from collections import defaultdict
from collections import namedtuple
from dataclasses import dataclass, field

from .graph_tools import make_path
from .graph_tools import make_montage_list

@dataclass
class SubWire:
    'Класс определяет характеристики отдельно провода у Жилы'
    length: float
    gauge: float

class Wire:
    """
    Класс Жила, содержит контакты, которые жила объединяет
    и характеристики участков провода между контактами.
    """
    def __init__(self, wire: str):
        self._contacts = {}
        self._wire = wire
        self._section = 0

    def is_multy_gauge(self):
        if not self._contacts:
            return False
        first_key = list(self._contacts.keys())[0]
        first_gauge = self._contacts[first_key].gauge
        return any((i.gauge != first_gauge for i in self._contacts.values()))

    def set_gauge(self, edge, gauge):
        self._contacts[edge].gauge = gauge

    def add_contacts(self, edge, length, gauge):
        if edge in self._contacts:
            raise Exception(edge, self._contacts, 'Контакт присутствует в списке контактов!')
        self._contacts[edge] = SubWire(length, gauge)

    def list_contacts(self):
        result = []
        for edge in self._contacts.keys():
            contact1, contact2 = edge
            if contact1 not in result:
                result.append(contact1)
            if contact2 not in result:
                result.append(contact2)
        return result

    def pair_contacts(self):
        return list(self._contacts.keys())

    def length(self, u, v):
        result = None
        if (v, u) in self._contacts:
            result = self._contacts[(v, u)].length
        elif (u, v) in self._contacts:
            result = self._contacts[(u, v)].length
        else:
            raise Exception(self._wire, u, v, self._contacts, 'Длинна не инициализировано для жилы!')
        return result

    def name(self):
        return self._wire

    def in_wire(self, u, v):
        return (v, u) in self._contacts or (u, v) in self._contacts

    def gauge(self, u, v):
        result = None
        if (v, u) in self._contacts:
            result = self._contacts[(v, u)].gauge
        elif (u, v) in self._contacts:
            result = self._contacts[(u, v)].gauge
        else:
            raise Exception(self._wire, u, v, self._contacts, 'Сечение не инициализировано для жилы!')
        return result

GraphContacts = namedtuple('GraphContacts', 'graph ending_contact gauge')

@dataclass
class SplitedWire:
    """
    Класс описывает множество контактов которые будут объеденены общей жилой,
    и, если такие определены, контакты которые олжны замыкать жилу
    """
    contacts: set
    ending_contact: list

class Wires:
    """
    Множество жил в шкафу. Данный класс инициализирует класс Wire
    """
    def __init__(self, devices, connected_contacts, cabine_definition):
        self._devices = devices
        self._connected_contacts = connected_contacts
        self._cabine_definition = cabine_definition
        self._device_section = {}
        self._wires = {}
        self._contact_wire = {}
        self._wg = WireGauge(self._connected_contacts, self._cabine_definition)

    def _make_splited_wire(self, wire: str):
        result = {}
        scheme_gauges = set()
        config_gauges = set() 
        for contact in self._wg.splited_contact(wire):
            gauges_contact = self._wg.config_gauges(wire, contact)
            config_gauges.update(gauges_contact)
            for gauge, contacts in self._wg.scheme_gauges(wire).items():
                if gauge in gauges_contact:
                    if gauge in result:
                        result[gauge].ending_contact.append(contact)
                    else:
                        result[gauge] = SplitedWire(contacts, [contact])
                scheme_gauges.add(gauge)
        if config_gauges != scheme_gauges:
            raise Exception(f"У жилы {wire} cечения конфига: {config_gauges=} и в схеме: {scheme_gauges=} не совпадают!")
        return result

    def _get_graph(self, G, wire: str):
        result = []
        if wire in self._wg.splited_wires():
            for gauge, splited_wire in self._make_splited_wire(wire).items():
                contacts = set(splited_wire.contacts)
                ending_contact = splited_wire.ending_contact
                contacts.update(ending_contact)
                subgraph = G[wire].subgraph(contacts).copy()
                result.append(GraphContacts(subgraph, ending_contact, gauge))
        else:
            ending_contact = self._cabine_definition.get_ending_contact(wire)
            gauge = self._wg.min_wire_gauge(wire)
            result.append(GraphContacts(G[wire], ending_contact, gauge))
        return result

    def _add_pair_contacts(self, wire: str, u, v, length, gauge):
        if wire not in self._wires:
            self._wires[wire] = Wire(wire)
        self._wires[wire].add_contacts((u, v), int(length), gauge)

    def _add_contacts_in_wires(self, wire: str, montage_list, gauge):
        for edge in make_path(montage_list):
            device1, contact1 = edge[0].split(':')
            device2, contact2 = edge[1].split(':')
            u = self._devices[device1].contact(contact1)
            v = self._devices[device2].contact(contact2)
            length = montage_list.get_edge_data(*edge)['weight']
            self._add_pair_contacts(wire, u, v, length, gauge)

    def init_wires(self, G):
        for wire in G:
            for graph_contacts in self._get_graph(G, wire):
                g = graph_contacts.graph
                ending_contact = graph_contacts.ending_contact
                montage_list = make_montage_list(g, wire, ending_contact)
                self._add_contacts_in_wires(wire, montage_list, graph_contacts.gauge)

    def wires(self):
        return self._wires

    def wire(self, wire: str):
        return self._wires[wire]


class WireGauge:
    def __init__(self, connected_contacts, cabine_definition):
        self._wires = self._init_wires(connected_contacts)
        self._contact_wire = self._init_contact_wire()
        self._wire_contact = self._init_wire_contact(cabine_definition)
        self._wire_gauges = self._init_wire_gauges(cabine_definition)
        self._min_wire_gauge = self._init_min_wire_gauge(connected_contacts)

    def _init_min_wire_gauge(self, connected_contacts):
        result = {}
        min_gauge = defaultdict(list)
        for c in connected_contacts:
            min_gauge[c.wire].append(c.section)
        for wire in min_gauge:
            result[wire] = min(min_gauge[wire])
        return result

    def _init_wires(self, connected_contacts):
        result = defaultdict(lambda: defaultdict(set))
        for c in connected_contacts:
            result[c.wire][c.section].add(f'{c.device}:{c.name}')
        return result

    def _init_contact_wire(self):
        result = {}
        for wire, gauges in self._wires.items():
            for gauge, contacts in gauges.items():
                for contact in contacts:
                    result[contact] = wire
        return result
    
    def _init_wire_contact(self, cabine_definition):
        result = defaultdict(set)
        if 'double_gauge' in cabine_definition.conf:
            for contact in cabine_definition.conf.double_gauge:
                wire = self.wire(contact)
                result[wire].add(contact)
        return result
    
    def _init_wire_gauges(self, cabine_definition):
        result = defaultdict(dict)
        if 'double_gauge' in cabine_definition.conf:
            for contact in cabine_definition.conf.double_gauge:
                wire = self.wire(contact)
                result[wire][contact] = set(cabine_definition.conf.double_gauge[contact])
        return result

    def wire(self, contact):
        "К какой жиле принадлежит контакт"
        result = None
        if contact in self._contact_wire:
            result = self._contact_wire[contact]
        return result

    def scheme_gauges(self, wire):
        "Словать сечений с множеством контактов"
        result = {}
        for gauge in sorted(self._wires[wire], key=lambda x: float(x)):
            result[gauge] = self._wires[wire][gauge]
        return result
    
    def config_gauges(self, wire, contact) -> set:
        "Какие сечения подключаются к определенному контакту у жилы (жила тут лишний аргумент)"
        return self._wire_gauges[wire][contact]
    
    def splited_wires(self):
        "Жилы которые должны в схемах иметь разные сечения. Определяется из cabine_definition.conf"
        return self._wire_contact
    
    def splited_contact(self, wire):
        "Множество кантактов которые разделяют жилу на участки разного сечения. Определены в cabine_definition.conf"
        return self._wire_contact[wire]

    def min_wire_gauge(self, wire) -> str:
        return self._min_wire_gauge[wire]


def make_wires(G, devices, connected_contacts, cabine_definition):
    wires = Wires(devices, connected_contacts, cabine_definition)
    wires.init_wires(G)
    return wires


# Генерируем список жил и устройства к которым они подключены
def make_list_wires(connected_contacts, cabine_definition):
    result = {}
    for contact in connected_contacts:
        if cabine_definition.is_one_contact_in_wire(contact.wire, contact.device, contact.name):
            continue
        if contact.wire not in result:
            result[contact.wire] = []
        result[contact.wire].append(contact.full_name)
    return result
