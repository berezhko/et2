#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas
import logging
from collections import defaultdict


# In[2]:


from os import listdir
from os.path import isfile, join


# In[3]:


from src.logging_config import setup_logging

app_name = "ФайлыБлокиAutocad"
setup_logging(app_name)

logger = logging.getLogger(__name__)
logger.info(f"Запуск приложения: {app_name}!")


# In[4]:


from src.lisp_template import create_autocad_block_device


# In[5]:


class ContactsPossition:
    def __init__(self, contacts):
        self.contacts = defaultdict(list)
        for c in contacts:
            sign = -1 if contacts[c][0] in ("В", "П") else 1
            if contacts[c][0] in ("В", "Н"):
                self.contacts[contacts[c][0]].append(
                    (c, contacts[c][1], sign * contacts[c][2])
                )
            else:
                self.contacts[contacts[c][0]].append(
                    (c, sign * contacts[c][1], contacts[c][2])
                )
        self._autocad_possition, self._size = self._init_autocad_possition()

    def _init_autocad_possition(self):
        result = {}
        size = {}
        for d in self.contacts:
            contacts = self.contacts[d]
            point = 5
            for c in sorted(contacts, key=lambda x: (x[1], x[2])):
                if d == "В":
                    result[c[0]] = (point, 37)
                if d == "Н":
                    result[c[0]] = (point, 5)
                if d == "П":
                    result[c[0]] = (37, point)
                if d == "Л":
                    result[c[0]] = (5, point)
                point += 10
            size[d] = point - 5
        return result, size

    def possitions(self):
        return self._autocad_possition

    def device_size(self):
        if all(
            [
                any(["В" in self._size, "Н" in self._size]),
                all(["П" not in self._size, "Л" not in self._size]),
            ]
        ):
            return (max([s for s in self._size.values()]), 42)
        elif all(
            [
                any(["П" in self._size, "Л" in self._size]),
                all(["В" not in self._size, "Н" not in self._size]),
            ]
        ):
            return (42, max([s for s in self._size.values()]))
        else:
            raise Exception(
                self._size.keys(), f"Неподдерживаемы направления устройства!"
            )


def read_device(mypath):
    devices = {}
    for file in [f for f in listdir(mypath) if isfile(join(mypath, f))]:
        file_name = join(mypath, file)
        sheet_names = pandas.ExcelFile(file_name).sheet_names
        if "Devices" in sheet_names and "Contacts" in sheet_names:
            df_dev = pandas.read_excel(file_name, sheet_name="Devices")
            df_con = pandas.read_excel(file_name, sheet_name="Contacts")
            for _, d in df_dev.iterrows():
                if d["Тип"].find("py") != -1:
                    if d["Тип"] in devices:
                        continue
                    contacts = {}
                    for _, c in df_con.iterrows():
                        contacts[str(c["Номер"])] = (
                            c["Монтаж"],
                            c["Положение X"],
                            c["Положение Y"],
                        )
                    devices[d["Тип"]] = contacts
    return devices


def save_xlsx(mypath, devices):
    for d, contacts in devices.items():
        file_name = join(mypath, f"{d}.xlsx")
        with pandas.ExcelWriter(file_name) as writer:
            b = []
            contacts_possition = ContactsPossition(contacts)
            for c, p in contacts_possition.possitions().items():
                b.append({"Контакт": c, "Положение X": p[0], "Положение Y": p[1]})
            contacts_df = pandas.DataFrame(b)
            contacts_df.to_excel(writer, sheet_name="Contacts", index=False)

            size = contacts_possition.device_size()
            geometry_df = pandas.DataFrame(
                [
                    {
                        "РазмерБлока X": size[0],
                        "РазмерБлока Y": size[1],
                        "ПоворотБлока": 0,
                    }
                ]
            )
            geometry_df.to_excel(writer, sheet_name="Geometry", index=False)
        print(file_name)


def save_dwg(devices):
    result = []
    point_x = 0
    for d, contacts in devices.items():
        contacts_possition = ContactsPossition(contacts)
        size = contacts_possition.device_size()
        result.append(
            f'(CreateBlockWithVertices "{d}" "Defpoints" {size[0]} {size[1]} \'('
        )
        for c, p in contacts_possition.possitions().items():
            result.append(f'  ("{c}" {p[0]} {p[1]})')
        result.append("))")
        result.append(f'(command "_insert" "{d}" \'({point_x} 0) 1 1 0)')
        point_x += size[0] + 10
    return result


# In[6]:


devices = read_device(
    "/home/ivan/autocad/config/Нижневартовская ШАОТ/Панели/01/Устройства/"
)
# save_xlsx("/home/ivan/autocad/config/Устройства/", devices)


# In[7]:


from src.station import config

station = config.get_station()


# In[8]:


from src.out_connect.outer_connection import OuterConnection

outer_connection = OuterConnection(station)


# In[20]:


contacts = outer_connection.contact_data


# In[28]:


cabine = "01"
a = {}
for d in outer_connection.device_data:
    if d.is_device() and d.cabin == cabine and d.man_art not in a:
        a[d.man_art] = (d, contacts.get_list_contact_in_device(cabine, d.device))


# In[33]:


for name, (d, cs) in a.items():
    num, alpha = [], []
    for c in cs:
        if c.clemma.isdecimal():
            num.append(c)
        else:
            alpha.append(c)
    print(name, f"{len(num)}/{len(alpha)}")


# In[10]:


print("\n".join(save_dwg(devices)))
