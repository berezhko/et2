from collections import namedtuple

from .wire import make_wires
from .wire import make_list_wires

from src.exception import SingleContactForWire

# Ищем устройства которые есть в a и нет в b
def not_founded_devices(a, b):
    result = {}
    for name in a:
        if name not in b:
            dev = name.split(':')
            if dev[0] not in result:
                result[dev[0]] = []
            result[dev[0]].append(dev[1])
    return result


def find_blank_device(contacts, wires):
    contacts_in_m = {}
    for contact in contacts:
        if contact.device_name not in contacts_in_m:
            contacts_in_m[contact.device_name] = []
        contacts_in_m[contact.device_name].append(contact.contact_name)
        
    contacts_in_s = {}
    for w in wires:
        for name in wires[w]:
            dev = name.split(':')
            if dev[0] not in contacts_in_s:
                contacts_in_s[dev[0]] = []
            contacts_in_s[dev[0]].append(dev[1])
            
    print('Не используемые в схемах устройства!')
    for dev in contacts_in_m:
        if dev not in contacts_in_s:
            print(dev)


def check_intersection_wires(wires):
    print('Перечекающаяся проводка!')
    skip_wires = []
    for wire in wires:
        contact_union_wire = wires[wire]
        for w in wires:
            if w == wire or w in skip_wires:
                continue
            compare_contacts = wires[w]
            a = set(contact_union_wire)
            b = set(compare_contacts)
            if a.intersection(b):
                print(wire, ' Intersection with: ', w, a.intersection(b))
        skip_wires.append(wire)


def check_scheme(contacts, wires, check_my_scheme=True):
    contacts_in_m = {}
    for contact in contacts:
        contacts_in_m[contact.full_name] = 1
        
    contacts_in_s = {}
    for w in wires:
        for name in wires[w]:
            contacts_in_s[name] = 2

    not_found = not_founded_devices(contacts_in_s, contacts_in_m)
    print('Не найден в монтажке контакт!')
    for i in sorted(not_found):
        print(i, sorted(not_found[i]))
    print('Done!\n')

    if check_my_scheme == True:
        not_found = not_founded_devices(contacts_in_m, contacts_in_s)
        print('Не найден в схеме контакт!')
        for i in sorted(not_found):
            print(i, sorted(not_found[i]))


def compare(w1, w2):
    result = True
    for w in w1:
        if w not in w2:
            result = False
            break
        else:
            d1 = w1[w]
            d2 = w2[w]
            for d in d1:
                if d not in d2:
                    result = False
                    break
    print(result)


# Код доблируется в классе Wires
# Составляем список жил обходя контакты устройства
def wires_list(Devices):
    result = {}
    for device_name in Devices:
        device = Devices[device_name]
        for contact in device.used_contacts():
            wire = contact.wire()
            if wire not in result:
                result[wire] = []
            result[wire].append(contact.full_name)
    return result


# Составляем список жил на основании графа, списка устройств и клеммников
# Используется для проверки функции wires_list(Devices)
def wires_list2(G, devices, connected_contacts, cabine_definition):
    result = {}
    wires = make_wires(G, devices, connected_contacts, cabine_definition).wires().values()
    for wire in wires:
        for contact in wire.list_contacts():
            if wire.name() not in result:
                result[wire.name()] = []
            result[wire.name()].append(contact.full_name)
    return result


def check_wires_generate_algoritm(devices, G, connected_contacts, cabine_definition):
    wires = make_list_wires(connected_contacts, cabine_definition)
    compare(wires, wires_list(devices))
    compare(wires_list(devices), wires)
    
    wires = wires_list2(G, devices, connected_contacts, cabine_definition)
    compare(wires, wires_list(devices))
    compare(wires_list(devices), wires)


def wires_with_one_contact(connected_contacts, cabine_definition):
    wires = make_list_wires(connected_contacts, cabine_definition)
    raise_exception = False
    for w in wires:
        if len(wires[w]) < 2:
            raise_exception = True
            dev, con = wires[w][0].split(':')
            print(f"('{w}', '{dev}', '{con}'),")
    if raise_exception:
        raise SingleContactForWire()


def get_wire_contacts(outer_connection, cabine, wires, f):
    """
    Создаем массив жил с информацией о кол-вах контактах,
    из именах, и листах в проекте где они используются.

    outer_connection: класс представляющий внешние сзязи программы
    cabine: номер шкафа, контакты которого обрабатываюся
    wires: class Wires из модуля wire.py
    f: фильтр количества контактов, которые необходимо обработать,
       например lambda x: len(x) > 3 - выбрать все, кол-во которых больше 3
    """
    Wire = namedtuple('Wire', 'wire count contacts pages')
    
    w = wires
    a = sorted(w, key=lambda w: w.name())
    b = sorted(a, key=lambda w: len(w.list_contacts()))
    
    result = []
    
    for wire in b:
        if f(wire.list_contacts()):
            out_contacts = []
            out_pages = []
            for contact in wire.list_contacts():
                out_contacts.append(contact.full_name)
                out_pages.append(outer_connection.get_page(cabine, contact.full_name))
            result.append(Wire(
                wire.name(),
                len(wire.list_contacts()),
                out_contacts,
                out_pages
            ))
    return result


def output_wire_contacts(count_columns, wires):
    """
    Печатаем жилы, контакты и листы в проекте, где они используются в табличном виде

    count_columns: кол-во столбцов контактов
    wires: массив жил, которые возвращает ф-ия get_wire_contacts
    """
    def spaces(count):
        return " " * count

    result = ""
    
    max_len_contact_page = 0
    max_len_wire = 0
    max_len_count = 0
    
    for wire in wires:
        max_len_contact_page = max([max_len_contact_page] + [len(c) + len(p) for c, p in zip(wire.contacts, wire.pages)])
        max_len_wire = max(max_len_wire, len(wire.wire))
        max_len_count = max(max_len_count, len(str(wire.count)))
    
    for wire in wires:
        output = ""
        page = set(wire.pages)
        if len(page) == 1:
            output += "+"
            output += spaces(max_len_count + 0 - len(str(wire.count)))  # Zero space before count
        else:
            output += spaces(max_len_count + 1 - len(str(wire.count)))  # One space before count
        output += f"{wire.count} "
        output += f"{wire.wire}:"
        output += spaces(max_len_wire + 1 - len(wire.wire))  # One space after wire:
        for i, contact_page in enumerate(zip(wire.contacts, wire.pages), start=1):
            contact, page = contact_page
            output += f"{contact}"
            output += spaces(max_len_contact_page + 1 - len(contact) - len(page))  # One space after contact
            output += f"({page})"
            if i != wire.count:
                output += ", "
            if i % count_columns == 0 and i != wire.count:
                output += "\n" + spaces(max_len_count + max_len_wire + 4)  # 4 = len("[+ ] : ")
        result += output + "\n"
    return result


def get_possitions_contacts_in_wires(outer_connection, cabine, wires, f):
    """
    Создаем массив жил с информацией о кол-вах контактах,
    и их координатах на схеме проекта.

    outer_connection: класс представляющий внешние сзязи программы
    cabine: номер шкафа, контакты которого обрабатываюся
    wires: class Wires из модуля wire.py
    f: фильтр количества контактов, которые необходимо обработать,
       например lambda x: len(x) > 3 - выбрать все, кол-во которых больше 3
    """
    Wire = namedtuple('Wire', 'wire count possitions')
    
    w = wires
    a = sorted(w, key=lambda w: w.name())
    b = sorted(a, key=lambda w: len(w.list_contacts()))
    
    result = []
    
    for wire in b:
        if f(wire.list_contacts()):
            out_possitions = []
            for contact in wire.list_contacts():
                out_possitions.append(outer_connection.get_possition(cabine, contact.full_name))
            result.append(Wire(
                wire.name(),
                len(wire.list_contacts()),
                out_possitions
            ))
    return result


def checking_wire_of_contacts(wires, file_prefix):
    """
    По информации о жилах (Имя, Количество объединенных ей контактах и
    Координатах контактах на схеме проекта) генерируем 2 скрипта. Первый
    создает Маркировку жил (создается множество слоев, с именами "Кол. ИмяЖилы",
    которые содержат полилинию, которая оъединяет все контакты жилы). Второй
    осуществляет проверку. При первом запуске все слои жил скрываются. При
    втором и последующем запускесе слои по одному показываются и таким образом
    можно осуществить проверка контактов жил.
    """
    from src.elements import AutocadElements, PolyLine, Layer
    from src import lisp_template
    
    result = AutocadElements()
    lay_names = []

    for wire in wires:
        lay_name = f'{wire.count} {wire.wire}'
        lay_names.append(lay_name)
        result.append(Layer(lay_name, '1'))
        possitions = sorted(wire.possitions, key=lambda p: (int(p[0]/10), int(p[1])))
        result.append(PolyLine(*possitions, w=(1, 0)))
    result.append(Layer(f'0'))
    result.save(f'{file_prefix} - Маркеровка.lsp')

    with open(f'{file_prefix} - Проверка.lsp', "w+", encoding="cp1251") as f:
        f.write(lisp_template.select_layers(f'"{'" "'.join(lay_names)}"'))