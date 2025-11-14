#!/usr/bin/env python
# coding: utf-8

# # Программы охватывающие внешние связи проекта

# In[1]:


import pandas
import shutil
import logging

from os.path import basename
from datetime import datetime
from collections import Counter
from collections import defaultdict


# In[2]:


from src.logging_config import setup_logging

unixtime = round(datetime.now().timestamp())
app_name = "ВнешниеПодключения"
setup_logging(app_name)

logger = logging.getLogger(__name__)
logger.info(f"Запуск приложения: {app_name}, выходные скрипты отмечены как {unixtime}")


# ## Подключение проектируемого объекта

# In[3]:


from src.station import config

station = config.get_station()


# In[4]:


main_file = station.scheme_file
cable_file = station.cable_set_file
output_dir = station.OUTPUT_DIR
plot_dir = station.PLOT_DIR


# ## Импортирование вспомогательных функций

# ### Функции работающие со структурой clemmnic_data

# In[5]:


from src.out_connect.pandas import make_clemmnic_list


# ### Функции работающие со структурой contact и device

# In[6]:


from src.out_connect.contact import make_contact_list
from src.out_connect.device import make_device_list


# ### Класс CableConnection формирующий кабеля

# In[7]:


from src.out_connect.cable_connection import make_cable_connection


# ### Функции работы с исходной структурой Pandas

# In[8]:


from src.out_connect.pandas import read_project_data


# ### Функции формарования КЖ и списка жил

# In[9]:


from src.out_connect.cable_journal import make_wires_journal
from src.out_connect.cable_journal import make_cable_journal
from src.out_connect.cable_journal import total_length_journal
from src.out_connect.cable_journal import count_section_journal
from src.out_connect.cable_journal import shrink_long_string


# ### Построение монтажных схем

# In[10]:


import src.out_connect.montage_cable as montage_cable
from src.out_connect import isolation_cables


# ### Прочие функции

# In[11]:


from src.station.misc import get_short_cabinet_name
from src.out_connect.clemmnic import used_clemms
from src.out_connect.pandas import used_wires

from src.out_connect.general import device_list
from src.out_connect.general import make_cabinet_table
from src.out_connect.general import view_devices_with_contacts
from src.out_connect.general import print_work_scheme
from src.out_connect.general import print_schemes_name

import src.plot_table as pl
from src.plot_table import fit_data

from src.elements import AutocadElements


# ## Чтение исходной схемы и инициализация основных структур

# In[12]:


project_data = read_project_data(station)


# In[13]:


contact_data = make_contact_list(project_data, station)
device_data = make_device_list(project_data, station)


# In[14]:


clemmnic_data = make_clemmnic_list(project_data, station)


# In[15]:


cables_collection = make_cable_connection(clemmnic_data, station)


# ### Отладочная информация о работе алгоритма

# In[16]:


columns_clemmnic_data = [
    "wire",
    "clemmnic",
    "clemma",
    "cabin",
    "cabel",
    "inner_wire",
    "section",
    "type_cabel",
    "process",
    "number",
    "direction",
]
pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data).sort_values(
    by=["cabin", "clemmnic", "clemma"]
).to_csv(f"{output_dir}/Отладка-{unixtime}.csv")


# #### Краткое содержание clemmnic_data

# In[17]:


pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)


# #### Клеммники с различающимися внешними и внутренними жилами

# In[18]:


def different_wires(station, clemmnic_data):
    df = pandas.DataFrame()
    for cabine in station.show_contacts_cabines():
        df = pandas.concat(
            [df, pandas.DataFrame(clemmnic_data.different_wires(cabine))]
        )
    return df


different_wires(station, clemmnic_data)


# #### Контакты, которые задублированы

# In[19]:


contact_data.check_intersection(station, device_data)


# #### Кабели, для которых не найдена пара

# In[20]:


pdm = pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)
pandas.set_option("display.max_rows", None)
not_defined_cable = pdm[(pdm.process == 0) & (~pdm.cabel.isna())].sort_values(
    by=["wire", "cabel", "cabin"]
)
not_defined_cable


# In[21]:


def check_cable(df):
    cable_not_define = []
    for i, row in df.iterrows():
        if row.cabel not in station.preset_cables():
            cable_not_define.append(row.cabel)
    if cable_not_define:
        print(df[df.cabel.isin(cable_not_define)].to_string())
        raise Exception(
            """Определи пары для всех направлений или спряч их в
        схеме! Направления, для которых нет пар могут быть только кабелями
        из других разделв проекта. И они должны быть явно указаны в методе
        station.preset_cables()"""
        )


# In[22]:


check_cable(not_defined_cable)


# #### Кабели, для которых нет напрвления

# In[23]:


pdm = pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)
pandas.set_option("display.max_rows", None)
pdm[(pdm.direction.isna()) & (~pdm.cabel.isna())]


# In[24]:


pandas.set_option("display.max_rows", 60)
pandas.get_option("display.max_rows")


# #### Краткое содержание cables_collection

# In[25]:


cables_collection.debug(unixtime)


# #### Длины направлений для внетренних и внешних участков

# In[26]:


from src.out_connect.misc import used_direction

used_direction(station, cables_collection)


# ## Список клеммников и жил в шкафах

# In[27]:


used_clemms(station, clemmnic_data, f"{plot_dir}/Схемы/Клеммники.xlsx")
used_wires(contact_data, clemmnic_data, f"{plot_dir}/Схемы/Жилы.xlsx")


# ## Общие данные

# ### Список шкафов

# In[28]:


def save_cabinet_table(station, file_name):
    config = station.conf.cabine_list
    columns = ["Номер", "Обозначение", "Наименование", "Примечание"]
    table_width = config.table_width
    header_table = [columns]
    rows_in_table = config.rows_in_table
    start_possition = {"X": config.start_possition[0], "Y": config.start_possition[1]}
    print_table1 = pandas.DataFrame(make_cabinet_table(station)).to_numpy()

    height = pl.HEIGHT
    pl.HEIGHT = config.height
    pl.plot_split_table(
        print_table1,
        header_table,
        table_width,
        rows_in_table,
        rows_in_table,
        start_possition,
        file_name,
        delta=config.delta,
        align=["c", "c", "l", "c"],
    )

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )

    pl.HEIGHT = height


# In[29]:


save_cabinet_table(
    station, f"{plot_dir}/Схемы/ОД. Печать списка шкафов для принципиалок.lsp"
)


# ### Заполнение листа общих данных

# In[30]:


print_work_scheme(
    station,
    f"{plot_dir}/Схемы/ОД. Рабочие, ссылочные и прилагаемые чертежи.lsp",
    20,
    292,
)


# ### Заполнение первых листов основного комплекта

# In[31]:


print_schemes_name(
    station,
    f"{plot_dir}/Схемы/ОД. Заполнение первых листов основного комплекта.lsp",
    -1000,
    -297,
    1,
)


# ### Список устройств с информацией о контактах

# #### Вывод в Autocad

# In[32]:


def plot_devices(station, data_pandas, file_name):
    config = station.conf.devices_list
    rows_in_first_sheet = config.rows_in_first_sheet
    rows_in_other_sheet = config.rows_in_other_sheet
    start_possition = {"X": config.start_possition[0], "Y": config.start_possition[1]}
    table_width = config.table_width
    ksize_font = 7 * [3.2 / 5]
    align = ["c", "l", "l", "l", "c", "l", "l"]

    data_numpy = data_pandas.to_numpy()
    header_table = [list(data_pandas.columns)]

    pl.plot_split_table(
        fit_data(
            data_numpy,
            table_width,
            ksize_font=ksize_font,
            delim=" ",
            add_blank_line=False,
        ),
        header_table,
        table_width,
        rows_in_first_sheet,
        rows_in_other_sheet,
        start_possition,
        file_name,
        delta=config.delta,
        align=align,
    )

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )


# In[33]:


plot_devices(
    station,
    device_list(station, contact_data, device_data),
    f"{plot_dir}/Схемы/ОД. Печать списка устойств c контактами для принципиалок.lsp",
)


# #### Вывод в Excel и Csv

# In[34]:


def used_devices_with_contacts(station, contact_data, device_data, file_name):
    with pandas.ExcelWriter(file_name) as writer:
        for cabin_num in station.show_contacts_cabines():
            closet_device = view_devices_with_contacts(
                station, contact_data, device_data, cabin_num, add_closet=False
            )
            if not closet_device.empty:
                cabin = get_short_cabinet_name(station, int(cabin_num))
                closet_device.to_excel(writer, sheet_name=cabin, index=False)


def used_devices_with_contacts_to_csv(station, contact_data, device_data, file_name):
    df = pandas.DataFrame()
    cabins = []
    for cabin_num in station.show_contacts_cabines():
        new_df = view_devices_with_contacts(
            station,
            contact_data,
            device_data,
            cabin_num,
            add_closet=False,
            add_blank_line=False,
        )
        df = pandas.concat([df, new_df])
        cabins += len(new_df) * [cabin_num]
    df["ШКАФ"] = cabins
    df.to_csv(file_name, index=False)

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.csv"
    )


# In[35]:


used_devices_with_contacts(
    station, contact_data, device_data, f"{plot_dir}/Схемы/Спецификация устойств.xlsx"
)

used_devices_with_contacts_to_csv(
    station,
    contact_data,
    device_data,
    f"{plot_dir}/Схемы/ОД. Печать списка устойств c контактами для принципиалок.csv",
)


# ## Формирование кабельно жирнала

# ### Список жил

# In[36]:


list_wires = make_wires_journal(station, cables_collection, clemmnic_data)

name_file = f"{output_dir}/Жилы-{unixtime}"
list_wires_pandas = pandas.DataFrame(list_wires)
list_wires_pandas.to_excel(name_file + ".xlsx", index=False)
list_wires_pandas.to_csv(name_file + ".csv", index=False)

list_wires_pandas.to_excel(f"{plot_dir}/КЖ/Excel Список жил.xlsx", index=False)

lisp_list_wires = pl.plot_table(
    shrink_long_string(list_wires_pandas.to_numpy()),
    [36, 36, 26, 25, 240, 32],
    align=["c", "c", "c", "c", "l", "c"],
)
AutocadElements(lisp_list_wires).save(f"{plot_dir}/КЖ/Печать списка жил.lsp")

list_wires_pandas


# ### Кабельный журнал

# In[37]:


cable_journal = make_cable_journal(station, cables_collection)

name_file = f"{output_dir}/КЖ-{unixtime}"
cable_journal_pandas = pandas.DataFrame(cable_journal)
cable_journal_pandas.to_excel(name_file + ".xlsx", index=False)
cable_journal_pandas.to_csv(name_file + ".csv", index=False)

list_wires_pandas.to_excel(f"{plot_dir}/КЖ/Excel Кабельный журнал.xlsx", index=False)

lisp_cable_journal = pl.plot_table(
    shrink_long_string(cable_journal_pandas.to_numpy()),
    [25, 35, 20, 120, 120, 15, 15, 15, 30],
    offset=(-395, 0),
    align=["c", "c", "c", "l", "l", "c", "c", "c", "c"],
)
AutocadElements(lisp_cable_journal).save(f"{plot_dir}/КЖ/Печать КЖ.lsp")

cable_journal_pandas


# ### Формирование схем кабельных связей

# In[38]:


from src.out_connect.cable_journal import CableLinks

lisp_cable_links = CableLinks(station, cables_collection).plot_cable_link()
AutocadElements(lisp_cable_links).save(
    f"{plot_dir}/КЖ/Печать схемы кабельных связей.lsp"
)
out = shutil.copyfile(
    f"{plot_dir}/КЖ/Печать схемы кабельных связей.lsp",
    f"{output_dir}/Печать схемы кабельных связей-{unixtime}.lsp",
)


# In[39]:


# Общий файл содержащий КЖ, Список жил и Схему кабельных связей
AutocadElements(lisp_cable_links + lisp_cable_journal + lisp_list_wires).save(
    f"{plot_dir}/КЖ/Общий скрипт кабельного журнала.lsp"
)


# ## Построения монтажных схем

# In[40]:


def montage_scheme(frame):
    montage_cable.station = station
    montage_cable.cables_collection = cables_collection
    montage_cable.contact_data = contact_data
    montage_cable.clemmnic_data = clemmnic_data

    montage = montage_cable.MontageCable(frame)
    montage_data = montage.get_montage()

    montage_sheets = montage.get_contents()
    montage_sheets_pandas = pandas.DataFrame(montage_sheets, index=["Листы"]).T
    summer = {"Шкафы": [], "Листы": []}
    for i, row in montage_sheets_pandas.iterrows():
        summer["Шкафы"].append(i)
        summer["Листы"].append(row["Листы"])

    print_table = pandas.DataFrame(summer).to_numpy()
    sheet_data = pl.plot_table(
        print_table, [120, 30], offset=(50, 350), align=["l", "l"]
    )

    AutocadElements(sheet_data + montage_data).save(
        f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.lsp"
    )
    shutil.copyfile(
        f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.lsp",
        f"{output_dir}/Монтажные схемы подключения кабелей-{unixtime}.lsp",
    )

    pandas.DataFrame(montage_cable.montage_scheme_array()).to_csv(
        f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.csv",
        sep=";",
        index=False,
    )
    shutil.copyfile(
        f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.csv",
        f"{output_dir}/Монтажные схемы подключения кабелей-{unixtime}.csv",
    )

    return montage_sheets_pandas


def save_cores_notes():
    montage_cable.station = station
    montage_cable.cables_collection = cables_collection
    montage_cable.contact_data = contact_data
    montage_cable.clemmnic_data = clemmnic_data

    montage_cable.output_clemmnics(
        0, 4, f"{plot_dir}/Схемы/Маркеровка жил на трубку 4мм (S жил до 4мм2).xlsx"
    )
    montage_cable.output_clemmnics(
        4,
        16,
        f"{plot_dir}/Схемы/Маркеровка жил на трубку 6мм и более (S жил от 4мм2 до 16мм2).xlsx",
    )


# ### Монтажные схемы

# In[41]:


montage_scheme(frame=montage_cable.A3)


# ### Маркеровка жил

# In[42]:


save_cores_notes()


# ### Протокол проверки изоляции кабелей

# In[43]:


if "isolation" in station.conf and station.conf.isolation == True:
    isolation = isolation_cables.Isolation(
        station,
        cables_collection,
        contact_data,
        clemmnic_data,
        generate_r=(
            station.conf.isolation_gen if "isolation_gen" in station.conf else False
        ),
    )
    pandas.DataFrame(isolation()).to_excel(
        f"{plot_dir}/Протокол проверки изоляции кабелей.xlsx", index=False
    )


# ## Инициализация кабелей в принципиальных схемах

# In[44]:


from src.out_connect.define_cables import (
    set_cable_name,
    get_cable_without_names,
    get_cable_with_name_equal_direction,
)


# In[45]:


cables_data = set_cable_name(station, cables_collection)


# In[46]:


get_cable_without_names(cables_data)


# In[47]:


get_cable_with_name_equal_direction(cables_data)


# In[48]:


def save_init_cables_name(cables_data):
    pandas.DataFrame(cables_data).to_csv(
        f"{plot_dir}/Схемы/Загрузка инициализированных кабелей в чертеж Autocad.txt",
        sep="\t",
        encoding="cp1251",
        index=False,
    )
    shutil.copyfile(
        f"{plot_dir}/Схемы/Загрузка инициализированных кабелей в чертеж Autocad.txt",
        f"{output_dir}/Загрузка инициализированных кабелей в чертеж Autocad-{unixtime}.txt",
    )


# In[49]:


save_init_cables_name(cables_data)


# ## Инициализация ссылок на листы

# In[50]:


from src.out_connect import define_reference


# In[51]:


init_reference = define_reference.init_reference(station, contact_data, clemmnic_data)
pandas.DataFrame(init_reference)


# In[52]:


pandas.DataFrame(init_reference).to_csv(
    f"{plot_dir}/Схемы/Загрузка инициализированных ссылок в чертеж Autocad.txt",
    sep="\t",
    encoding="cp1251",
    index=False,
)


# ## Спецификация

# ### Длины и количество участнов

# In[53]:


total_length = total_length_journal(station, cables_collection)
pandas.DataFrame(total_length, index=["Длинна"]).T.to_excel(
    f"{plot_dir}/Итоговые длины.xlsx"
)
pandas.DataFrame(total_length, index=["Длинна"]).T.to_csv(
    f"{output_dir}/Итоговые длины-{unixtime}.csv"
)
pandas.DataFrame(total_length, index=["Длинна"]).T


# In[54]:


count_section = count_section_journal(cables_collection)
pandas.DataFrame(count_section, index=["Количество участков"]).T.to_csv(
    f"{output_dir}/Итоговое количество участков-{unixtime}.csv"
)
pandas.DataFrame(count_section, index=["Количество участков"]).T


# ### Количество и деаметр отверстий в шкафах

# In[55]:


from src.holes import calc_count_hole
from src.holes import diameter_for_cabinet


def count_cables_in_cabiten(cabinet):
    result = {}
    for cable in cables_collection.cables():
        if cabinet not in cables_collection.get_cabins_by_cable(cable):
            continue
        result[cable] = cables_collection.section(cable)
    preset_cables = station.preset_cables()
    for cable in preset_cables:
        if cabinet not in preset_cables.directions(cable):
            continue
        result[cable] = (
            preset_cables.get_type(cable) + " " + preset_cables.get_cores_gauge(cable)
        )
    return result


# In[56]:


for cabinet in station.cabine_holes():
    print(get_short_cabinet_name(station, int(cabinet)), end=":\t")
    for d, c in calc_count_hole(cabinet, cables_collection).items():
        print("М" + d, "-", str(c) + "шт", end=", ")
    print()


# In[57]:


for cabinet in station.cabine_holes():
    print(get_short_cabinet_name(station, int(cabinet)), end=":\t")
    for d, c in diameter_for_cabinet(cabinet, cables_collection).items():
        print(d + "мм" + " - " + str(c) + "шт", end=", ")
    print()


# ### Список устройств в шкафах

# #### Вывод в Excel

# In[58]:


from src.out_connect.specification import (
    used_devices_for_specification,
    summary_equipment_schedule,
    generate_equipment_config,
)


# In[59]:


used_devices_for_specification(
    station,
    clemmnic_data.get_list_cabine(),
    device_data,
    f"{plot_dir}/Спецификация устойств для спецификации.xlsx",
)

pandas.DataFrame(
    summary_equipment_schedule(station, clemmnic_data, device_data)
).to_excel(
    f"{plot_dir}/Сводна ведомость устойств спецификации.xlsx",
    sheet_name="Сводна ведомость",
)

if station.conf.cabines.generate_equipment_config:
    generate_equipment_config(
        clemmnic_data, device_data, f"{plot_dir}/Шкаф/Устройства/"
    )


# ### Печеть спецификации устройств

# In[60]:


from src.out_connect.specification import (
    spds_specification,
    spds_specification_excel,
    spds_specification_array,
)

spds_array = spds_specification_array(
    station, cables_collection, clemmnic_data, device_data.get_device_for_spec
)


# #### Вывод в AutoCad

# In[61]:


spds_specification(spds_array, f"{plot_dir}/Спецификация к разделу.lsp")
_ = shutil.copyfile(
    f"{plot_dir}/Спецификация к разделу.lsp",
    f"{output_dir}/Спецификация к разделу-{unixtime}.lsp",
)


# #### Вывод в Excel

# In[62]:


spds_specification_excel(
    spds_array, f"{plot_dir}/Спецификация к разделу.xlsx", copy_to_csv=True
)
_ = shutil.copyfile(
    f"{plot_dir}/Спецификация к разделу.csv",
    f"{output_dir}/Спецификация к разделу-{unixtime}.csv",
)


# ## Печать графа объединяющего шкафы и кабель-каналы

# In[63]:


from src.out_connect.length_cable.length import ClosetsGraph
from src.graph_view import GraphView


# In[64]:


import os.path

if os.path.exists(station.CABINE_FILE):
    closet_graph = ClosetsGraph(station)
    cable_chanel = GraphView(closet_graph.cabine).plot(
        closet_graph.boxes, closet_graph.closet_graph, (20, 150)
    )

    AutocadElements(cable_chanel).save(
        f"{plot_dir}/Схемы/Шкафы/Схема графа кабель-каналов.lsp"
    )
    out = shutil.copyfile(
        f"{plot_dir}/Схемы/Шкафы/Схема графа кабель-каналов.lsp",
        f"{output_dir}/Схема графа кабель-каналов-{unixtime}.lsp",
    )


# # Отладка

# In[65]:


import unittest
from src.test import TestOutput


# In[66]:


TestOutput.UNIXTIME = unixtime
TestOutput.OUTPUT_DIR = output_dir
TestOutput.TEST_CASE = station.test_case()
TestOutput.generate_tests()
_ = unittest.main(argv=[""], verbosity=1, exit=False)
