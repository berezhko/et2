from src.misc import eq
from src.elements import Line
from src.elements import Text
from src.elements import Circle
from src.elements import TextStyle
from src.elements import Block

class OrderBackContacts:
    def __init__(self, contact):
        self._contact = contact

    def _is_single(self, back_contacts):
        return len(back_contacts) == 1

    def _is_multy(self, back_contacts):
        return len(back_contacts) == 2

    def _order_multy_contacts(self, contact, back_contacts):
        b1 = back_contacts[0]
        b2 = back_contacts[1]
        result = None
        if float(contact.wire_gauge(b1)) > float(contact.wire_gauge(b2)):
            result = [b1, b2]
        elif float(contact.wire_gauge(b2)) > float(contact.wire_gauge(b1)):
            result = [b2, b1]
        elif b2.full_name > b1.full_name:
            result = [b1, b2]
        else:
            result = [b2, b1]
        return result

    def __call__(self):
        back_contacts = self._contact.back_connection()
        if self._is_single(back_contacts):
            return back_contacts
        elif self._is_multy(back_contacts):
            return self._order_multy_contacts(self._contact, back_contacts)
        else:
            raise Exception(self._contact, back_contacts, 'У контакта число подключений не равно 1 или 2!')


class Autocad:
    contact_radius = 3
    font_size_gauge = 2
    font_size_contact = 3
    font_size_wire = 3
    
    def __init__(self, device, device_type):
        self._device = device
        self.device_type = device_type

    def plot_contact(self, possition, contact_name):
        x, y = possition
        result = [Text((x, y), contact_name, self.font_size_contact, 0, '_MC')]
        return result

    def _mark_wire_section(self, wire_section, angle, x, y):
        result = []
        if eq(wire_section, 0.75):
            pass
        elif eq(wire_section, 1.5):  # Slash
            result += [Line((x-1, y-1), (x+1, y+1))]
        elif eq(wire_section, 2.5):  # Double Slash
            if angle == 90:
                result += [
                    Line((x-1, y-0.5), (x+1, y+1.5)),
                    Line((x-1, y-1.5), (x+1, y+0.5)),
                ]
            else:
                result += [
                    Line((x-0.5, y-1), (x+1.5, y+1)),
                    Line((x-1.5, y-1), (x-0.5, y+1)),
                ]
        else:
            result += [Text((x, y), str(int(wire_section)), self.font_size_gauge, angle, '_MC', 'Standard Shrink')]
        return result

    def _plot_back_contact(self, possition, align, back_address, wire_section, direction):
        x, y = possition
        dx, dy = direction
        angle = 0
        if dx == 0:
            angle = 90
        result = []
        if eq(wire_section, 0.75) or eq(wire_section, 1.5) or eq(wire_section, 2.5):
            result += [Line((x, y), (x+dx, y+dy))]
        else:
            result += [Line((x, y), (x+dx/5, y+dy/5))]
            result += [Line((x+4*dx/5, y+4*dy/5), (x+dx, y+dy))]
        result += self._mark_wire_section(wire_section, angle, x+dx/2.0, y+dy/2.0)
        result += [Text((x+dx*11/10., y+dy*11/10.), back_address, self.font_size_wire, angle, align, 'Standard Shrink')]
        return result

    def _get_contact(self, contact, contacts_position):
        if contact.contact_name in contacts_position:
            result = contacts_position[contact.contact_name]
        elif contact.contact_name in self._device.get_all_contacts():
            result = (None, None)
            #  print(
            #      self._device._name, self.device_type, 
            #      f"Контакт {contact.contact_name} найден в подустройстве!"
            #  )
        else:
            print(self._device.get_all_contacts())
            raise Exception(contact.contact_name, self._device.name(), 'Контакт не найден в устройстве!')
        return result

    def _try_check_direction(self, direction):
        if direction not in ('П', 'Л', 'В', 'Н'):
            raise Exception(direction, "Направление указано неверно. Допустимые значения - ('П', 'Л', 'В', 'Н')!")

    def _get_justify(self, direction):
        if direction in ('Н', 'Л'):
            sign = -1
            justify = '_MR' # Середина-вправо
        elif direction in ('В', 'П'):
            sign = 1
            justify = '_ML' # Середина-влево
        return (sign, justify)

    def _plot_back_contacts(self, contact, x1, y1, dx, dy, align):
        x2, y2 = x1+dx, y1+dy
        result = []
        back_contacts = OrderBackContacts(contact)
        for back_contact in back_contacts():
            back_address = contact.address(back_contact)
            wire_section = contact.wire_gauge(back_contact)
            result += [Line((x1, y1), (x2, y2))]
            result += self._plot_back_contact((x2, y2), align, back_address, wire_section, (dx, dy))
            x2, y2 = x2+abs(dy), y2-abs(dx)
        return result

    def _plot_back_contacts_2_direction(self, possition, contact):
        x1, y1 = possition
        self._try_check_direction(contact.direction)
        sign, justify = self._get_justify(contact.direction)
        align = justify
        x1, y1 = x1, y1 + sign*self.contact_radius
        dx, dy = 0, sign*5
        return self._plot_back_contacts(contact, x1, y1, dx, dy, align)

    def _plot_back_contacts_4_direction(self, possition, contact):
        x1, y1 = possition
        self._try_check_direction(contact.direction)
        sign, justify = self._get_justify(contact.direction)
        align = justify
        if contact.direction in ('Н', 'В'):
            y1 = y1 + sign*self.contact_radius
            dx, dy = 0, sign*5
        else: # ('П', 'Л')
            x1 = x1 + sign*self.contact_radius
            dx, dy = sign*5, 0
        return self._plot_back_contacts(contact, x1, y1, dx, dy, align)

    def _get_contact_possition(self, possition, contact):
        x, y = self._get_contact(contact, self._contacts)
        if x is None or y is None:
            return (None, None)
        else:
            return (possition[0]+x, possition[1]+y)

    def plot_back_contacts(self, possition, contact):
        return self._plot_back_contacts_4_direction(possition, contact)

    def plot_montage_scheme(self, possition):
        result = self.plot_device(possition)
        for contact in self._device.contacts():
            x, y = self._get_contact_possition(possition, contact)
            if x is None or y is None:
                continue
            result += self.plot_contact((x, y), contact.contact_name)
            if contact.contact_connected():
                result += self.plot_back_contacts((x, y), contact)
        return result

    def contacts(self):
        return list(self._contacts.keys())


class AutocadTerminalBlock(Autocad):
    def __init__(self, device, device_type):
        super().__init__(device, device_type)
        self._direction = ''

    def _plot_terminal_cell(self, possition, dx, dy):
        x, y = possition
        return [Line((x, y), (x+dx, y), (x+dx, y+dy), (x, y+dy), c=True)]

    def _try_check_all_direction_equal(self, direction, old_direction):
        if old_direction != '' and direction != old_direction:
            raise Exception(self._device.name(), direction, old_direction, "В клеммника контакты подключаются с разных сторон!")
        return direction

    def _cell_size(self):
        return (5, 42)

    def plot_back_contacts(self, possition, contact):
        return self._plot_back_contacts_2_direction(possition, contact)

    def plot_device(self, possition):
        x, y = possition
        result = []
        for contact_name in sorted(self._contacts.keys(), key=int):
            contact = self._device.contact(contact_name)
            width = 2*self._cell_size()[0] if contact.count_back_connection() == 2 else self._cell_size()[0]
            result += self._plot_terminal_cell((x, y), width, self._cell_size()[1])
            x, y = x + width, y
        return result

    def _calc_contacts_position(self):
        result = {}
        contact_names = []
        cell_size = self._cell_size
        pos_x = 0
        for contact in self._device.contacts():
            contact_names.append(contact.contact_name)

        for contact_name in map(str, sorted(list(map(int, contact_names)))):
            contact = self._device.contact(contact_name)
            direction = contact.direction
            self._direction = self._try_check_all_direction_equal(direction, self._direction)

            width = 2*cell_size()[0] if contact.count_back_connection() == 2 else cell_size()[0]
            if direction in ('В', 'П'):
                result[contact.contact_name] = (pos_x + cell_size()[0]/2.0, 37)
            if direction in ('Н', 'Л'):
                result[contact.contact_name] = (pos_x + cell_size()[0]/2.0, 5)
            pos_x += width
        return result

    def get_length(self):
        result = 0
        cell_size = self._cell_size()[0]
        for contact in self._device.contacts():
            width = 2*cell_size if contact.count_back_connection() == 2 else cell_size
            result += width
        return result

    def init_contacts_position(self):
        self._contacts = self._calc_contacts_position()


class AutocadRelaySimple_v2(Autocad):
    def __init__(self, device, device_type):
        super().__init__(device, device_type)

    def _get_group(self, number):
        a = [1, 2, 4]
        return list(map(str, (map(lambda x: x+number, a))))

    def _count_connection(self):
        result = {}
        for group in [10, 20, 30, 40]:
            result[group] = 0
            for contact_name in self._get_group(group):
                if self._device.contact(contact_name).contact_connected():
                    result[group] += 1
        return result
        
    def _get_size(self, number):
        return {0: 10, 2: 20, 3:30}[number]

    def _calc_width_relay(self):
        count_connected = self._count_connection()
        result = 0
        for group in count_connected:
            result += self._get_size(count_connected[group])
        return result

    def _calc_contacts_position(self):
        count_connected = self._count_connection()
        dx = 5
        result = {'A1': (5, 5), 'A2': (self._calc_width_relay()-5, 5)}
        for group in count_connected:
            if count_connected[group] == 0:
                dx += 10
            elif count_connected[group] == 3:
                for contact_name in self._get_group(group):
                    result[contact_name] = (dx, 37)
                    dx += 10
            else:
                for contact_name in self._get_group(group):
                    if self._device.contact(contact_name).contact_connected():
                        result[contact_name] = (dx, 37)
                        dx += 10
        return result

    def _plot_contact_addition_info(self, x, y, contact):
        result = [Circle((x, y), self.contact_radius)]
        if contact.contact_name == 'A1' or contact.contact_name == 'A2':
            result += [Line((x, y+3), (x, y+5.5))]
        elif contact.contact_name[1] == '1':
            result += [Line((x, y-3), (x, y-4.5))]
        elif contact.contact_name[1] == '2':
            a, b = self._start_point(contact)
            result += [
                Line((x-(b-a), y-10), (x, y-10)),
                Line((x, y-3), (x, y-10)),
            ]
        elif contact.contact_name[1] == '4':
            a, b = self._start_point(contact)
            result += [
                Line((x-(b-a), y-14), (x, y-14)),
                Line((x, y-3), (x, y-14)),
            ]
        return result

    def _start_point(self, contact):
        contacts_position = self._calc_contacts_position()
        my_position = contacts_position[contact.contact_name]
        group_position = contacts_position[contact.contact_name[0]+'1']
        return (group_position[0]+1.5, my_position[0])

    def plot_device(self, possition):
        x, y = possition
        dx, dy = self._calc_width_relay(), 42
        result = [
            Line((x, y), (x+dx, y), (x+dx, y+dy), (x, y+dy), c=True),
            Block((x+dx/2., y), 'py_relay_block_coil'),
        ]
        
        dx = 5
        count_connected = self._count_connection()
        for group in count_connected:
            result += [Block((x+dx, y), f"py_relay_block_{group}")]
            if group == 10:
                result += [
                    Block((x+dx, y), 'py_relay_block_a1'),
                    Line((x+dx+1.5, y+12), (x+self._calc_width_relay()/2.0 - 3, y+12)),
                ]
            if group == 40:
                result += [
                    Block((x+self._calc_width_relay() - 5, y), 'py_relay_block_a2'),
                    Line((x+self._calc_width_relay()/2.0 + 3, y+12), (x+self._calc_width_relay() - 6.5, y+12)),
                ]
            dx += self._get_size(count_connected[group])
        return result

    def plot_montage_scheme(self, possition):
        result = self.plot_device(possition)
        for contact in self._device.contacts():
            if not contact.contact_connected():
                continue
            x, y = self._get_contact_possition(possition, contact)
            if x is None or y is None:
                continue
            result += self.plot_contact((x, y), contact.contact_name)
            result += self._plot_contact_addition_info(x, y, contact)
            if contact.contact_connected():
                result += self.plot_back_contacts((x, y), contact)
        return result

    def get_length(self):
        return self._calc_width_relay()

    def init_contacts_position(self):
        self._contacts = self._calc_contacts_position()


class AutocadUnknown(Autocad):
    def __init__(self, device, device_type):
        super().__init__(device, device_type)

    def plot_device(self, possition):
        # plot rectangle
        x, y = possition
        length, height = self._calc_device_length()
        result = [
            Line((x, y), (x+length, y), (x+length, y+height), (x, y+height), c=True),
        ]
        return result

    def _calc_device_length(self):
        length_up = 0
        length_down = 0
        for contact in self._device.contacts():
            if contact.direction in ('В', 'П'):
                length_up += 10
            else: # contact.direction in ('Н', 'Л'):
                length_down += 10
        length = max(10, length_up, length_down)
        result = (length, 42)
        return result

    def _calc_contacts_position(self):
        result = {}
        x_up = 5
        x_down = 5
        number_contacts = []
        string_contacts = []
        for contact in self._device.contacts():
            if contact.contact_name.isnumeric():
                number_contacts.append(contact)
            else:
                string_contacts.append(contact)

        def _collect_result(contacts, key, x_up, x_down):
            for contact in sorted(contacts, key=lambda x: key(x.contact_name)):
                if contact.direction in ('В', 'П'):
                    result[contact.contact_name] = (x_up, 37)
                    x_up += 10
                else: # contact.direction in ('Н', 'Л'):
                    result[contact.contact_name] = (x_down, 5)
                    x_down += 10  
            return (x_up, x_down)

        x_up, x_down = _collect_result(number_contacts, int, x_up, x_down)
        x_up, x_down = _collect_result(string_contacts, str, x_up, x_down)

        return result

    def plot_back_contacts(self, possition, contact):
        return self._plot_back_contacts_2_direction(possition, contact)

    def get_length(self):
        return self._calc_device_length()[0]

    def init_contacts_position(self):
        self._contacts = self._calc_contacts_position()


class AutocadBlock(Autocad):
    def __init__(self, device, device_type, block):
        super().__init__(device, device_type)
        self._block_name = block.block_name
        self._contacts = block.contacts
        self._length = block.length

    def plot_device(self, possition):
        result = [Block(possition, self._block_name)]
        return result

    def get_length(self):
        return self._length

    def init_contacts_position(self):
        pass
