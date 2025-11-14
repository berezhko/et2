#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas
from collections import namedtuple
from collections import Counter
from os.path import basename
from datetime import datetime
import shutil
from math import sqrt
from pprint import pprint


# In[2]:


from src.out_connect.pandas import read_project_data
from src.out_connect.pandas import make_clemmnic_list
from src.misc import isNaN
from src.station.misc import get_short_cabinet_name

from src.out_connect import montage_cable

from src.out_connect.contact import make_contact_list
from src.out_connect.cable_connection import make_cable_connection


# In[3]:


from src.station import config

station = config.get_station()
unixtime = round(datetime.now().timestamp())


# In[4]:


plot_dir = station.PLOT_DIR
output_dir = station.OUTPUT_DIR


# In[5]:


project_data = read_project_data(station)


# In[6]:


montage_cable.station = station
montage_cable.contact_data = make_contact_list(project_data)
montage_cable.clemmnic_data = make_clemmnic_list(project_data, station)

montage_cable.cables_collection = make_cable_connection(
    montage_cable.clemmnic_data, station
)


# In[7]:


from src.out_connect.cable import is_kvvg
from src.out_connect.cable import is_vvg
from src.out_connect.cable import get_diameter_kvvg
from src.out_connect.cable import get_diameter_vvg


# In[8]:


def diameters_for_cables(cabinet, cables, cables_collection):
    def calc_diameter(type_cab, num, section):
        def k_shield(s):
            return 1.15 if len(type_cab) >= len(s) and type_cab[0 : len(s)] == s else 1

        result = 12
        if is_kvvg(type_cab):
            result = k_shield("КВВГЭ") * get_diameter_kvvg(int(num), float(section))
        elif is_vvg(type_cab):
            result = k_shield("ВВГЭ") * get_diameter_vvg(int(num), float(section))
        return int(result + 1.0)

    result = []
    for cable in cables:
        if cable not in cables_collection.cables():
            continue
        if cabinet not in cables_collection.get_cabins_by_cable(cable):
            continue

        section, type_cab = cables_collection.section(cable)
        num = cables_collection.count_wires(cable)
        diameter = calc_diameter(type_cab, num, section)
        result.append(diameter)
    return result


def radius(s):
    return sqrt(s / 3.14)


def diametr(s):
    return sqrt(4 * s / 3.14)


def get_clemmnics(cabin):
    return montage_cable.clemmnic_data.get_list_terminals(cabin)


# In[9]:


def square(cabin, clemmnic):
    cable_list = get_cable_list(cabin, clemmnic)
    return sum(
        map(
            lambda x: x**2,
            diameters_for_cables(cabin, cable_list, montage_cable.cables_collection),
        )
    )


# In[10]:


def get_cable_list(cabin, clemmnic):
    cable_list = set()
    for clemma in montage_cable.clemmnic_data:
        if clemma.cabin != cabin:
            continue
        if clemma.clemmnic != clemmnic:
            continue
        if isNaN(clemma.cabel):
            continue

        cable_list.add(clemma.cabel)
    return cable_list


# In[11]:


def sum_square(cabin, clemmnics):
    if not clemmnics:
        clemmnics = get_clemmnics(cabin)
    return sum([square(cabin, c) for c in clemmnics])


# In[12]:


data = [
    {"01": []},
    {"03": []},
    {"04": []},
    {"05": ["XA3", "XA4", "XA5", "XA6", "XA7"]},
    {"05": ["X1", "X2", "X3", "X4", "X5", "XA1", "XA2", "XV1", "XV2"]},
    {"06": ["X1", "X2", "X3", "X4", "X5", "X6"]},
    {"06": ["X10", "X11", "X12", "X13", "X14", "X7", "X9", "X8"]},
    {"07": []},
    {"08": []},
    {"11": []},
    {"13": []},
    {"19": []},
    {"20": []},
    {"24": ["X1"]},
    {"24": ["X2"]},
]


# In[13]:


for d in data:
    for cabin, clemmnics in d.items():
        print(
            f"{get_short_cabinet_name(station, int(cabin)):.<8} \u2300 = {int(diametr(sum_square(cabin, clemmnics))):>3} [мм]"
        )


# In[14]:


cabin = "07"

print(get_clemmnics(cabin))

cable_list = set()
for clemmnic in get_clemmnics(cabin):
    for cable in get_cable_list(cabin, clemmnic):
        cable_list.add(cable)
Counter(diameters_for_cables(cabin, cable_list, montage_cable.cables_collection))
