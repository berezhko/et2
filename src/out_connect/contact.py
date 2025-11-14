from collections import Counter
from dataclasses import dataclass, field
from typing import Union, List, Tuple

from src.misc import isNaN
from src.station.misc import pairs_number_and_short_name

from .misc import what


@dataclass(order=True, frozen=True)
class Contact():
    cabin: str = field(repr=False)
    device: str = field(repr=False)
    clemma: str
    inner_wire: str = field(compare=False, repr=False)
    section: Union[str, float] = field(compare=False, repr=False)
    possition: Tuple[float] = field(compare=False, repr=False)
    page: str = field(compare=False)


class ContactList(List[Contact]):
    def get_list_device_in_cabin(self, cabin):
        result = set()
        for i in self:
            if i.cabin == cabin:
                result.add(i.device)
        return result

    def get_list_contact_in_device(self, cabin, device):
        result = ContactList()
        for i in self:
            if i.cabin == cabin and i.device == device:
                result.append(i)
        return result

    def _get_attribute(self, cabin, name_contact, param):
        result = None
        device, clemma = name_contact.split(":")
        for i in self:
            if i.cabin == cabin and i.device == device and i.clemma == clemma:
                result = what(i, param)
                break
        return result

    def page_contact(self, cabin, name_contact):
        return self._get_attribute(cabin, name_contact, 'page')

    def possition_contact(self, cabin, name_contact):
        return self._get_attribute(cabin, name_contact, 'possition')
        

    def _check_intersection(self, device_data, cabin):
        'Ищет контакты корорые упомянаяются в проекте 2 и более раз'
        result = ''
        for device in device_data.get_device(cabin):
            list_device = self.get_list_contact_in_device(cabin, device.device)
            counter = Counter(list_device)
            for contact, count in counter.items():
                if count > 1:
                    for c in list_device:
                        if c == contact:
                            result += f'{device.device=}, {c.clemma=}, {c.page=}, {c.inner_wire=}\n'
        return result

    def check_intersection(self, station, device_data):
        import sys
        for short_name, cabin_num in pairs_number_and_short_name(station).items():
            intersection = self._check_intersection(device_data, cabin_num)
            if intersection:
                print(short_name, file=sys.stderr)
                print(intersection, file=sys.stderr)

    # get_device(contact_data, '06', '1347')
    # 'KL84:14'
    def get_device(self, cabin, back_wire):
        result = back_wire
        for contact in self:
            if contact.cabin == cabin and contact.inner_wire == back_wire:
                result = f'{contact.device}:{contact.clemma}'
                break
        return result


def make_contact_list(df, station):
    from src.out_connect.pandas import make_contact_list, make_contact
    df = make_contact_list(df, station).fillna('')
    result = ContactList()
    for index, row in df.iterrows():
        result.append(Contact(*make_contact(row)))
    return result