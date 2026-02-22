#!/usr/bin/env python
# coding: utf-8

# # Программы охватывающие внешние связи проекта

# In[1]:


import pandas
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


# ## Импортир функций проекта

# ### Построение клеммников

# In[5]:


from src.out_connect.pandas import make_clemmnic_list


# ### Постоение контактов и устройств

# In[6]:


from src.out_connect.contact import make_contact_list
from src.out_connect.device import make_device_list


# ### Формирование кабеля

# In[7]:


from src.out_connect.cable_connection import make_cable_connection


# ### Чтение исходных данных

# In[8]:


from src.out_connect.pandas import read_project_data


# ### Общие данные

# In[9]:


from src.out_connect.general import (
    device_list,
    make_cabinet_table,
    view_devices_with_contacts,
    print_work_scheme,
    print_schemes_name,
    save_cabinet_table,
    plot_devices,
)


# ### Кабельные журнал

# In[10]:


from src.out_connect.cable_journal import (
    make_wires_journal,
    make_cable_journal,
    total_length_journal,
    count_section_journal,
    shrink_long_string,
    get_table_cable_journal_f7_1,
    get_table_total_length,
    CableLinks,
)


# ### Монтажные схемы

# In[11]:


import src.out_connect.montage_cable as montage_cable
from src.out_connect import isolation_cables


# ### Выгрузка кебелей в в схему

# In[12]:


from src.out_connect.define_cables import (
    set_cable_name,
    get_cable_without_names,
    get_cable_with_name_equal_direction,
)


# ### Спецификация

# In[13]:


from src.out_connect.specification import (
    used_devices_for_specification,
    summary_equipment_schedule,
    generate_equipment_config,
    spds_specification,
    spds_specification_excel,
    spds_specification_array,
)


# ### Прочие функции

# In[14]:


from src.station.misc import get_short_cabinet_name
from src.out_connect.clemmnic import used_clemms
from src.out_connect.pandas import used_wires

import src.plot_table as pl
from src.plot_table import fit_data

from src.elements import AutocadElements

from src.misc import (
    safe_to_csv,
    safe_to_excel,
    safe_excel_writer,
    copy_file,
    file_exist,
)


# ## Чтение исходной схемы и инициализация основных структур

# In[15]:


project_data = read_project_data(station)


# In[16]:


contact_data = make_contact_list(project_data, station)
device_data = make_device_list(project_data, station)


# In[17]:


clemmnic_data = make_clemmnic_list(project_data, station)


# In[18]:


cables_collection = make_cable_connection(clemmnic_data, station)


# ### Отладочная информация о работе алгоритма

# In[19]:


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
safe_to_csv(
    pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data).sort_values(
        by=["cabin", "clemmnic", "clemma"]
    ),
    f"{output_dir}/Отладка-{unixtime}.csv",
)


# #### Краткое содержание clemmnic_data

# In[20]:


pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)


# #### Клеммники с различающимися внешними и внутренними жилами

# In[21]:


def different_wires(station, clemmnic_data):
    df = pandas.DataFrame()
    for cabine in station.show_contacts_cabines():
        df = pandas.concat(
            [df, pandas.DataFrame(clemmnic_data.different_wires(cabine))]
        )
    return df


different_wires(station, clemmnic_data)


# #### Контакты, которые задублированы

# In[22]:


contact_data.check_intersection(station, device_data)


# #### Кабели, для которых не найдена пара

# In[23]:


pdm = pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)
pandas.set_option("display.max_rows", None)
not_defined_cable = pdm[(pdm.process == 0) & (~pdm.cabel.isna())].sort_values(
    by=["wire", "cabel", "cabin"]
)
not_defined_cable


# In[24]:


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


# In[25]:


check_cable(not_defined_cable)


# #### Кабели, для которых нет напрвления

# In[26]:


pdm = pandas.DataFrame(clemmnic_data, columns=columns_clemmnic_data)
pandas.set_option("display.max_rows", None)
pdm[(pdm.direction.isna()) & (~pdm.cabel.isna())]


# In[27]:


pandas.set_option("display.max_rows", 60)
pandas.get_option("display.max_rows")


# #### Краткое содержание cables_collection

# In[28]:


cables_collection.debug(unixtime)


# #### Длины направлений для внетренних и внешних участков

# In[29]:


from src.out_connect.misc import used_direction

used_direction(station, cables_collection)


# ## Список клеммников и жил в шкафах

# In[30]:


used_clemms(station, clemmnic_data, f"{plot_dir}/Схемы/Клеммники.xlsx")
used_wires(contact_data, clemmnic_data, f"{plot_dir}/Схемы/Жилы.xlsx")


# ## Общие данные

# ### Список шкафов

# In[31]:


file_name = f"{plot_dir}/Схемы/ОД. Печать списка шкафов для принципиалок.lsp"
save_cabinet_table(station, file_name)
copy_file(file_name, output_dir, unixtime)


# ### Заполнение листа общих данных

# In[32]:


print_work_scheme(
    station, f"{plot_dir}/Схемы/ОД. Рабочие, ссылочные и прилагаемые чертежи.lsp"
)


# ### Заполнение первых листов основного комплекта

# In[33]:


print_schemes_name(
    station, f"{plot_dir}/Схемы/ОД. Заполнение первых листов основного комплекта.lsp"
)


# ### Список устройств с информацией о контактах

# #### Вывод в Autocad

# In[34]:


file_name = (
    f"{plot_dir}/Схемы/ОД. Печать списка устойств c контактами для принципиалок.lsp"
)
plot_devices(
    station,
    device_list(station, contact_data, device_data),
    file_name,
)
copy_file(file_name, output_dir, unixtime)


# #### Вывод в Excel и Csv

# In[35]:


def used_devices_with_contacts(station, contact_data, device_data, file_name):
    with safe_excel_writer(file_name) as writer:
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
    safe_to_csv(df, file_name, index=False)

    copy_file(file_name, output_dir, unixtime)


# In[36]:


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

# In[37]:


list_wires = make_wires_journal(station, cables_collection, clemmnic_data)

name_file = f"{output_dir}/Жилы-{unixtime}"
list_wires_pandas = pandas.DataFrame(list_wires)
safe_to_excel(list_wires_pandas, name_file + ".xlsx", index=False)
safe_to_csv(list_wires_pandas, name_file + ".csv", index=False)

safe_to_excel(list_wires_pandas, f"{plot_dir}/КЖ/Excel Список жил.xlsx", index=False)
list_wires_pandas


# ### Кабельный журнал

# In[38]:


cable_journal = make_cable_journal(station, cables_collection)

name_file = f"{output_dir}/КЖ-{unixtime}"
cable_journal_pandas = pandas.DataFrame(cable_journal)
safe_to_excel(cable_journal_pandas, name_file + ".xlsx", index=False)
safe_to_csv(cable_journal_pandas, name_file + ".csv", index=False)

safe_to_excel(
    list_wires_pandas, f"{plot_dir}/КЖ/Excel Кабельный журнал.xlsx", index=False
)
cable_journal_pandas


# In[39]:


all_scheme_cable_journal = pl.plot_configured_table(
    station.conf.cable_journal.cable_journal_f7_1,
    get_table_cable_journal_f7_1(cable_journal),
    f"{plot_dir}/КЖ/Печать КЖ Ф7.lsp",
)
all_scheme_cable_journal += pl.plot_configured_table(
    station.conf.cable_journal.total_length,
    get_table_total_length(station, cables_collection),
    f"{plot_dir}/КЖ/Печать КЖ общие длины кабелей.lsp",
)
if station.conf.cable_journal.wires_journal.print:
    all_scheme_cable_journal += pl.plot_configured_table(
        station.conf.cable_journal.wires_journal,
        list_wires_pandas.to_numpy(),
        f"{plot_dir}/КЖ/Печать КЖ список жил.lsp",
    )


# ### Формирование схем кабельных связей

# In[40]:


if station.conf.cable_journal.cable_links.print:
    lisp_cable_links = CableLinks(
        station, cables_collection, station.conf.cable_journal.cable_links
    ).plot_cable_link()
    file_name = f"{plot_dir}/КЖ/Печать схемы кабельных связей.lsp"
    AutocadElements(lisp_cable_links).save(file_name)
    copy_file(file_name, output_dir, unixtime)
    all_scheme_cable_journal += lisp_cable_links


# In[41]:


# Общий файл содержащий КЖ, Список жил и Схему кабельных связей
AutocadElements(all_scheme_cable_journal).save(
    f"{plot_dir}/КЖ/Общий скрипт кабельного журнала.lsp"
)


# ## Построения монтажных схем

# In[42]:


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

    file_name = f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.lsp"
    AutocadElements(sheet_data + montage_data).save(file_name)
    copy_file(file_name, output_dir, unixtime)

    file_name = f"{plot_dir}/Монтажки/Монтажные схемы подключения кабелей.csv"
    df_montage_cable = pandas.DataFrame(montage_cable.montage_scheme_array())
    safe_to_csv(df_montage_cable, file_name, sep=";", index=False)
    copy_file(file_name, output_dir, unixtime)

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

# In[43]:


montage_scheme(frame=montage_cable.A3)


# ### Маркеровка жил

# In[44]:


save_cores_notes()


# ### Протокол проверки изоляции кабелей

# In[45]:


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
    safe_to_excel(
        pandas.DataFrame(isolation()),
        f"{plot_dir}/Протокол проверки изоляции кабелей.xlsx",
        index=False,
    )


# ## Инициализация кабелей в принципиальных схемах

# In[46]:


cables_data = set_cable_name(station, cables_collection)


# In[47]:


get_cable_without_names(cables_data)


# In[48]:


get_cable_with_name_equal_direction(cables_data)


# In[49]:


def save_init_cables_name(cables_data):
    file_name = (
        f"{plot_dir}/Схемы/Загрузка инициализированных кабелей в чертеж Autocad.txt"
    )
    safe_to_csv(
        pandas.DataFrame(cables_data),
        file_name,
        sep="\t",
        encoding="cp1251",
        index=False,
    )
    copy_file(file_name, output_dir, unixtime)


# In[50]:


save_init_cables_name(cables_data)


# ## Инициализация ссылок на листы

# In[51]:


from src.out_connect import define_reference


# In[52]:


init_reference = define_reference.init_reference(station, contact_data, clemmnic_data)
pandas.DataFrame(init_reference)


# In[53]:


safe_to_csv(
    pandas.DataFrame(init_reference),
    f"{plot_dir}/Схемы/Загрузка инициализированных ссылок в чертеж Autocad.txt",
    sep="\t",
    encoding="cp1251",
    index=False,
)


# ## Спецификация

# ### Длины и количество участнов

# In[54]:


total_length = total_length_journal(station, cables_collection)
safe_to_excel(
    pandas.DataFrame(total_length, index=["Длинна"]).T,
    f"{plot_dir}/Итоговые длины.xlsx",
)
safe_to_csv(
    pandas.DataFrame(total_length, index=["Длинна"]).T,
    f"{output_dir}/Итоговые длины-{unixtime}.csv",
)
pandas.DataFrame(total_length, index=["Длинна"]).T


# In[55]:


count_section = count_section_journal(cables_collection)
safe_to_csv(
    pandas.DataFrame(count_section, index=["Количество участков"]).T,
    f"{output_dir}/Итоговое количество участков-{unixtime}.csv",
)
pandas.DataFrame(count_section, index=["Количество участков"]).T


# ### Количество и деаметр отверстий в шкафах

# In[56]:


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


# In[57]:


for cabinet in station.cabine_holes():
    print(get_short_cabinet_name(station, int(cabinet)), end=":\t")
    for d, c in calc_count_hole(cabinet, cables_collection).items():
        print("М" + d, "-", str(c) + "шт", end=", ")
    print()


# In[58]:


for cabinet in station.cabine_holes():
    print(get_short_cabinet_name(station, int(cabinet)), end=":\t")
    for d, c in diameter_for_cabinet(cabinet, cables_collection).items():
        print(d + "мм" + " - " + str(c) + "шт", end=", ")
    print()


# ### Список устройств в шкафах

# #### Вывод в Excel

# In[59]:


used_devices_for_specification(
    station,
    clemmnic_data.get_list_cabine(),
    device_data,
    f"{plot_dir}/Спецификация устойств для спецификации.xlsx",
)

safe_to_excel(
    pandas.DataFrame(summary_equipment_schedule(station, clemmnic_data, device_data)),
    f"{plot_dir}/Сводна ведомость устойств спецификации.xlsx",
    sheet_name="Сводна ведомость",
)

if station.conf.cabines.generate_equipment_config:
    generate_equipment_config(
        clemmnic_data, device_data, f"{plot_dir}/Шкаф/Устройства/"
    )


# ### Печеть спецификации устройств

# In[60]:


spds_array = spds_specification_array(
    station, cables_collection, clemmnic_data, device_data.get_device_for_spec
)


# #### Вывод в AutoCad

# In[61]:


file_name = f"{plot_dir}/Спецификация к разделу.lsp"
spds_specification(spds_array, file_name, station.conf.specification)
copy_file(file_name, output_dir, unixtime)


# #### Вывод в Excel

# In[62]:


file_name_xlsx = f"{plot_dir}/Спецификация к разделу.xlsx"
spds_specification_excel(spds_array, file_name_xlsx, copy_to_csv=True)

file_name = f"{plot_dir}/Спецификация к разделу.csv"
copy_file(file_name, output_dir, unixtime)


# ## Печать графа объединяющего шкафы и кабель-каналы

# In[63]:


from src.out_connect.length_cable.length import ClosetsGraph
from src.graph_view import GraphView


# In[64]:


if file_exist(station.CABINE_FILE):
    closet_graph = ClosetsGraph(station)
    cable_chanel = GraphView(closet_graph.cabine).plot(
        closet_graph.boxes, closet_graph.closet_graph, (20, 150)
    )
    file_name = f"{plot_dir}/Схемы/Шкафы/Схема графа кабель-каналов.lsp"
    AutocadElements(cable_chanel).save(file_name)
    copy_file(file_name, output_dir, unixtime)


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
