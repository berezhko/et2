#!/usr/bin/env python
# coding: utf-8

# # Программа генерирующая документацию на шкафы и панели

# In[1]:


import pandas
import shutil
import logging
from collections import deque
from collections import defaultdict

from os.path import basename

import networkx as nx
from datetime import datetime


# In[2]:


from src.logging_config import setup_logging

unixtime = round(datetime.now().timestamp())
app_name = "Шкафы"
setup_logging(app_name)

logger = logging.getLogger(__name__)
logger.info(f"Запуск приложения: {app_name}, выходные скрипты отмечены как {unixtime}")


# ## Подключение объекта

# In[3]:


from src.station import config

station = config.get_station()


# In[4]:


import sys

if __name__ == "__main__" and sys.argv[0][-8:] == "Шкафы.py":
    if len(sys.argv) == 1:
        raise Exception(sys.argv, "Не определен номер шкафа!")

    cabine_definition = station.get_cabine_data(sys.argv[1])
else:
    cabine_definition = station.get_cabine_data(config.get_default_cabin())


READ_WIRES_FROM_FILE = cabine_definition.conf.wires_from_files
READ_CLOSET_STRUCT_FROM_FILE = cabine_definition.conf.closet_struct_from_files
WORK_CABINE = cabine_definition.get_cabine_number()
closet_file = cabine_definition.closet_file

output_dir = station.OUTPUT_DIR
plot_dir = f"{station.PLOT_DIR}/Шкаф/{WORK_CABINE}"
graph_dir = f"{cabine_definition.conf.graph_dir}/{WORK_CABINE}"

all_lisp_data = []


# ## Подключение вспомогательных функций

# ### Функции для работы со структурой pandas

# In[5]:


from src.out_connect.pandas import get_inner_clemma
from src.out_connect.pandas import get_outer_clemma

from src.cabin.pandas import make_contacts_list
from src.cabin.pandas import make_boxes_list
from src.cabin.pandas import make_su_device_list
from src.cabin.pandas import make_connected_contact_list


# ### Функции для формирования графа монтажа устройств

# In[6]:


from src.cabin.graph_tools import make_path
from src.cabin.graph_tools import make_montage_list
from src.cabin.graph_tools import generate_graph_devices


# ### Функции выполняющие различные проверки с схемах

# In[7]:


from src.cabin.checking import check_intersection_wires
from src.cabin.checking import find_blank_device
from src.cabin.checking import check_scheme
from src.cabin.checking import wires_with_one_contact
from src.cabin.checking import check_wires_generate_algoritm
from src.cabin.checking import output_wire_contacts
from src.cabin.checking import get_wire_contacts
from src.cabin.checking import get_possitions_contacts_in_wires
from src.cabin.checking import checking_wire_of_contacts


# ### Функции присвоения номеров ссылкам на устройства

# In[8]:


from src.cabin.define_reference import read_reference_data
from src.cabin.define_reference import create_number_reference


# ### Прочие функции

# In[9]:


import src.plot_table as pl
from src.plot_table import fit_data

from src.elements import AutocadElements

from src.holes import calc_count_hole

from src.cabin.specification import su_to_eskd
from src.cabin.specification import device_specification
from src.cabin.specification import enclosure_specification

from src.edge import make_edges
from src.edge import calc_distance

from src.cabin.device import construct_devices
from src.cabin.wire import make_wires
from src.cabin.wire import make_list_wires

from src.out_connect.outer_connection import OuterConnection

from src.misc import safe_to_csv
from src.misc import safe_to_excel
from src.misc import safe_excel_writer


# ## Чтание схемы и подготовка основных структур

# In[10]:


outer_connection = OuterConnection(station)

pandas_clemma = get_inner_clemma(outer_connection.project_data, WORK_CABINE)
pandas_clemma_outside = get_outer_clemma(outer_connection.project_data, WORK_CABINE)


# In[11]:


connected_contacts = make_connected_contact_list(pandas_clemma, pandas_clemma_outside)


# In[12]:


boxes = make_boxes_list(closet_file)
contacts = make_contacts_list(closet_file)
su_device = make_su_device_list(closet_file, cabine_definition.specification)


# In[13]:


global_edges = make_edges(
    boxes,
    contacts,
    f"{graph_dir}/pickle/global_edges.pickle",
    READ_CLOSET_STRUCT_FROM_FILE,
)


# In[14]:


closet_graph = nx.Graph()
closet_graph.add_weighted_edges_from(global_edges.weighted_edges())


# In[15]:


wires = make_list_wires(connected_contacts, cabine_definition)
check_intersection_wires(wires)
find_blank_device(contacts, wires)
check_scheme(contacts, wires, check_my_scheme=False)
wires_with_one_contact(connected_contacts, cabine_definition)


# In[16]:


# Вывод жил с количеством контактоб больше 2
# for w in wires:
#    if len(wires[w]) > 2:
#        print(w, wires[w])


# In[17]:


# %prun -s time G = generate_graph_devices
G = generate_graph_devices(
    graph_dir,
    make_list_wires(connected_contacts, cabine_definition),
    closet_graph,
    from_files=READ_WIRES_FROM_FILE,
)


# In[18]:


devices = construct_devices(
    G, su_device, contacts, connected_contacts, cabine_definition
)


# In[19]:


check_wires_generate_algoritm(devices, G, connected_contacts, cabine_definition)


# In[20]:


checking_wire_of_contacts(
    get_possitions_contacts_in_wires(
        outer_connection,
        WORK_CABINE,
        make_wires(G, devices, connected_contacts, cabine_definition).wires().values(),
        lambda x: len(x) > 1,
    ),
    f"{station.PLOT_DIR}/Схемы/Контакты жил шкафа {WORK_CABINE}",
)

print(
    output_wire_contacts(
        5,
        get_wire_contacts(
            outer_connection,
            WORK_CABINE,
            make_wires(G, devices, connected_contacts, cabine_definition)
            .wires()
            .values(),
            lambda x: len(x) > 3,
        ),
    )
)


# ## Генерация раздела "Подключения проводок"

# ### Функции Подключения проводок

# In[21]:


def ordered_device_output(su_device):
    collection_data = {}
    for i in su_device.get_devices():
        if i.row not in collection_data:
            collection_data[i.row] = []
        if i.name not in collection_data[i.row]:
            collection_data[i.row].append(i.name)
    result = []
    for k in sorted(collection_data):
        result.append((k, collection_data[k]))
    return result


# Выводим устройства из массива row_devices в диапазоне от a до b
# (a - включено, b - не включено).
# Осуществляется перебор элементов из row_devices, начиная с a и заканчивая b.
def iterate_range(row_devices, a, b):
    result = []
    stop_skiped = True
    for device in row_devices:
        if device == b:
            break
        if device == a:
            stop_skiped = False
        if stop_skiped is True:
            continue
        result.append(device)
    return result


# Расчет количества переносов и дистанции между устройствами
# Функция расчитывает остаток отрезка при расстановке элементов интревалом в 10мм.
# А затем этот остоток делин количество элеменов и добавляет полученное число к 10мм,
# тем самым осуществляеся выравнивание расстановке элементов на схеме по правому и левому краю.
# В хвосте элементы не выравниваются, а ставятся как есть, с нтервалом в 10мм.
def calc_clearance(devices, row_devices, format_output):
    not_found_end = "1"
    found_end = "2"
    length = 0
    result = {}

    count = 0
    start_device = row_devices[0]
    stop_device = not_found_end
    row = 1

    for i, device in enumerate(row_devices, start=1):
        if row not in result:
            result[row] = {}

        length = length + devices[device].get_length() + 10
        if length >= format_output:
            stop_device = device
            stop_length = length - (devices[device].get_length() + 10)
            if (i - count - 1) != 0:  # Столько влезло устройств в линия
                clearance = (format_output - stop_length) / (i - count - 1) + 10
            else:
                clearance = 10  # Для очень длинных устройств которые не влезли в линию
            for dev in iterate_range(row_devices, start_device, stop_device):
                result[row][dev] = int(clearance)

            row += 1
            start_device = stop_device
            stop_device = found_end
            length = devices[device].get_length() + 10
            count = i

    if length < format_output:
        if stop_device == not_found_end:
            if len(row_devices) - 1 != 0:
                clearance = (format_output - length) / (len(row_devices) - 1) + 10
            else:
                clearance = 10
            for device in iterate_range(row_devices, start_device, stop_device):
                result[row][device] = int(clearance)
        else:
            result[row] = {}
            for device in iterate_range(row_devices, start_device, stop_device):
                result[row][device] = int(10)

    return result


def print_assembling_devices(devices, su_device, wiring_format):
    start_x = wiring_format.x
    start_y = wiring_format.y
    format_output = wiring_format.size

    if not "offset_y" in wiring_format:
        offset_y_in_new_page = 90
        offset_y_from_line_in_same_page = 132
        offset_y_free_space_for_signature_contact = 62
        border_y_output_format = 0
    else:
        offset_y = wiring_format.offset_y
        offset_y_in_new_page = offset_y.new_page
        offset_y_from_line_in_same_page = offset_y.from_line_in_same_page
        offset_y_free_space_for_signature_contact = (
            offset_y.free_space_for_signature_contact
        )
        border_y_output_format = 10

    height = offset_y_in_new_page
    x, y = start_x, start_y - height
    lisp = []
    row_pages = defaultdict(set)
    first_page = 2
    page = 0

    for row_number, row_devices in ordered_device_output(su_device):
        rows_output = calc_clearance(devices, row_devices, format_output[0])
        for row in rows_output:
            row_pages[row_number].add(first_page + page)
            length_last_device = 0
            for device in rows_output[row]:
                lisp += devices[device].plot_montage_scheme((x, y))
                clearance = rows_output[row][device]
                x = x + devices[device].get_length() + clearance
                length_last_device = devices[device].get_length()
            # Делаем перенос на новую строку, только если напечатали устройства
            # А для длинных устройств делаем 2 и более переносов
            length_last_device += format_output[0]
            while length_last_device - format_output[0] > 0:
                x, y = start_x, y - offset_y_from_line_in_same_page
                height += offset_y_from_line_in_same_page
                if (
                    height + offset_y_free_space_for_signature_contact
                    >= format_output[1]
                ):
                    page += 1
                    height = offset_y_in_new_page
                    y = (
                        start_y
                        - height
                        - page * (format_output[1] + border_y_output_format)
                    )
                length_last_device -= format_output[0]

    result = []
    for row_number, pages in row_pages.items():
        result.append(
            {
                "Ряд": "Ряд " + str(row_number),
                "Листы": "5." + ", 5.".join(map(str, pages)),
            }
        )
    print(pandas.DataFrame(result))

    global all_lisp_data
    all_lisp_data += lisp

    AutocadElements(lisp).save(f"{plot_dir}/Подключения проводок {WORK_CABINE}.lsp")

    _ = shutil.copyfile(
        f"{plot_dir}/Подключения проводок {WORK_CABINE}.lsp",
        f"{output_dir}/Подключения проводок {WORK_CABINE}-{unixtime}.lsp",
    )


# ### Подключения проводок

# In[22]:


def wiring_connect(devices, su_device):
    wiring_format = cabine_definition.wiring_connect_format()
    print_assembling_devices(devices, su_device, wiring_format)


# In[23]:


wiring_connect(devices, su_device)


# ## Генерация раздела "Соединения проводок"

# In[24]:


def _sort_contacts(wire, reverse):
    def _swap(a, b, reverse):
        return (a, b) if reverse else (b, a)

    def _in(a, c):
        return any((a in i for i in c))

    c = deque(sorted(wire.pair_contacts(), key=lambda x: wire.gauge(x[0], x[1])))

    len_c = len(c)
    result = []
    u_prev, v_prev = None, None
    while c:
        u, v = c.popleft()
        if u_prev is None and v_prev is None:  # При первом входе в цикл
            # Начинаем всегда с точки имеющей одно вхождение
            while _in(u, c) and _in(v, c):
                c.append((u, v))
                u, v = c.popleft()
            if _in(
                u, c
            ):  # Если u в с, то эта точка должна быть второй (у нее есть пара)
                u_prev, v_prev = v, u
            else:  # _in(v, c), так как после while кто-то один не в c
                u_prev, v_prev = u, v
            result.append((u_prev, v_prev))
            continue
        # Ищем следующую пару для предыдущих вершин
        while all([u_prev != u, v_prev != v, u_prev != v, v_prev != u]):
            c.append((u, v))
            u, v = c.popleft()
        # При необходимости меняем местами u, v
        if u == v_prev or v == u_prev:
            u_prev, v_prev = _swap(v, u, reverse)
        else:  # u == u_prev or v == v_prev:
            u_prev, v_prev = _swap(u, v, reverse)
        result.append((u_prev, v_prev))
    if len(result) != len_c:
        raise Exception(
            len_c,
            len(result),
            result,
            f"Длинна входного массива отличается от длинный выходного!",
        )
    return result


def _get_connection_wires(wires, filt, reverse):
    def round_decimal(length: float) -> int:
        return round((length + 60) / 10) * 10

    result = []
    for count, wire in enumerate(wires, start=1):
        end = len(wire.pair_contacts())
        if filt(wire.is_multy_gauge()):
            continue
        contacts = _sort_contacts(wire, reverse=reverse)
        for i, (u, v) in enumerate(contacts, start=1):
            a = {}
            a["Жила"] = wire.name()
            a["Адрес 1"] = u.full_name
            a["Адрес 2"] = v.full_name
            a["Маркировка адреса 1"] = u.address(v)
            a["Маркировка адреса 2"] = v.address(u)
            a["Дл. мм"] = round_decimal(wire.length(u, v))
            a["Сеч. мм2"] = wire.gauge(u, v)
            a["Данные провода"] = (
                f'{cabine_definition.get_type_wire(wire.name())} 1x{a["Сеч. мм2"]}'
            )
            a["№ жилы"] = str(i) + "/" + str(end)
            a["Номер"] = count
            result.append(a)
    return result


def build_internal_installation(G, devices, connected_contacts):
    wires = (
        make_wires(G, devices, connected_contacts, cabine_definition).wires().values()
    )
    reverse = cabine_definition.conf.reverse_wires_connection
    single = _get_connection_wires(wires, lambda x: x, reverse)
    multy = _get_connection_wires(wires, lambda x: not x, reverse)
    result = sorted(
        single, key=lambda x: (x["Сеч. мм2"], x["Жила"], x["Номер"])
    ) + sorted(multy, key=lambda x: (x["Жила"], x["Номер"]))
    return result


def pandas_internal_installation(internal_inst):
    columns = [
        "Жила",
        "Адрес 1",
        "Адрес 2",
        "Маркировка адреса 1",
        "Маркировка адреса 2",
        "Данные провода",
        "№ жилы",
        "Номер",
    ]
    df = pandas.DataFrame(internal_inst)
    df["Номер"] = range(1, len(df["Номер"]) + 1)
    return pandas.DataFrame(df, columns=columns)


def pandas_internal_installation_brief(internal_inst):
    return pandas.DataFrame(
        pandas_internal_installation(internal_inst),
        columns=["Жила", "Адрес 1", "Адрес 2", "Данные провода", "№ жилы"],
    )


# In[25]:


internal_inst = build_internal_installation(G, devices, connected_contacts)
safe_to_csv(
    pandas_internal_installation(internal_inst),
    f"{output_dir}/Соединения проводок {WORK_CABINE}-{unixtime}.csv",
    index=False,
)
pandas_internal_installation(internal_inst)


# In[26]:


safe_to_csv(
    pandas_internal_installation_brief(internal_inst),
    f"{output_dir}/Соединения_проводок_кратко {WORK_CABINE}-{unixtime}.csv",
    index=False,
)
pandas_internal_installation_brief(internal_inst)


# In[27]:


def wiring_join(internal_inst):
    rows_in_first_sheet = 56
    rows_in_other_sheet = 66
    table_width = [18, 18, 18, 38, 38, 30, 15, 10]
    start_possition = {"X": 210, "Y": 20}

    df = pandas_internal_installation(internal_inst)

    numpy_data = df.to_numpy()
    header_table = [list(df.columns)]
    file_name = f"{plot_dir}/Соединения проводок {WORK_CABINE}.lsp"

    global all_lisp_data
    all_lisp_data += pl.plot_split_table(
        numpy_data,
        header_table,
        table_width,
        rows_in_first_sheet,
        rows_in_other_sheet,
        start_possition,
        file_name,
        delta=25,
    )
    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )


# In[28]:


wiring_join(internal_inst)


# ## Генерация раздела "Спецификация шкафа"

# ### Функции расчета дополнительных материалов

# #### Длины жил внутренних проводок

# In[29]:


def total_length(G, devices, connected_contacts):
    result = {}
    for wire in build_internal_installation(G, devices, connected_contacts):
        section = wire["Данные провода"]
        length = int(wire["Дл. мм"])
        if section not in result:
            result[section] = 0
        result[section] += length

    return result


# In[30]:


total_length(G, devices, connected_contacts)


# #### Количество втулочных наконечников

# In[31]:


def sleeve_count(G, devices, connected_contacts):
    def accumulate(key, param, count):
        if key not in param:
            param[key] = 0
        param[key] += count

    temp = {}
    for wire in build_internal_installation(G, devices, connected_contacts):
        section = str(wire["Сеч. мм2"])
        wire_name = str(wire["Жила"])
        key = (wire_name, section)
        accumulate(key, temp, 1)

    result = {}
    for key, count in temp.items():
        wire, section = key
        count1 = 2
        count2 = count - 1
        key1 = f"1x{section}"
        key2 = f"2x{section}"
        accumulate(key1, result, count1)
        if count2 != 0:
            accumulate(key2, result, count2)
    return result


# In[32]:


sleeve_count(G, devices, connected_contacts)


# #### Количество гермовводов

# In[33]:


def cable_input_count(cables_collection):
    result = {}

    for d, c in calc_count_hole(WORK_CABINE, cables_collection).items():
        result["М" + d] = c
    return result


# #### Расчет плотности заполнения коробов по типам

# In[34]:


# Расчет плотности заполнения коробов по типам
def calc_fulness_box(G, closet_graph, box):
    # Словарь с коробами и массивом жил в них уложенными
    fulness_box = {}
    for wire in G:
        ggg = make_montage_list(G, wire, cabine_definition.get_ending_contact(wire))
        for edge in make_path(ggg):
            u, v = edge
            path = nx.dijkstra_path(closet_graph, u, v, "weight")
            for b in path:
                if (
                    b == path[0] or b == path[-1]
                ):  # Убрали контакты, оставив только короба
                    continue

                if b not in fulness_box:
                    fulness_box[b] = []
                fulness_box[b].append(wire)

    # Вычисляем максимальные плотности жил в различных типах коробов
    result = {}
    for i in box:
        b = box[i]
        size = (
            int(calc_distance(b["Лево"], b["Право"])),
            int(calc_distance(b["Низ"], b["Верх"])),
        )
        count_wire = 0
        if i in fulness_box:
            count_wire = len(fulness_box[i])
        if size not in result:
            result[size] = count_wire
        else:
            result[size] = count_wire if count_wire > result[size] else result[size]

    return result


# Доработать, с учетом действующих размеров коробов
# calc_fulness_box(G, closet_graph, boxes.to_dict())
# ### Спецификация

# In[35]:


pandas.DataFrame(
    su_device, columns=["manufacture", "info", "articul", "count", "unit", "name"]
)


# ### Вывод в Autocad

# In[36]:


def eskd_specification(su_device, cabine, equipment=False):
    rows_in_first_sheet = 56
    rows_in_other_sheet = 66
    start_possition = {"X": 210, "Y": 614}
    table_width = [6, 6, 8, 70, 63, 10, 22]
    ksize_font = 3 * [3.5 / 5] + [3.8 / 5] + 3 * [3.5 / 5]
    align = ["c", "c", "c", "l", "l", "c", "c"]

    eskd_pandas = su_to_eskd(su_device, cabine, equipment)
    eskd_numpy = eskd_pandas.to_numpy()
    header_table = [list(eskd_pandas.columns)]
    file_name = f"{plot_dir}/Спецификация устройств {WORK_CABINE}.lsp"

    global all_lisp_data
    all_lisp_data += pl.plot_split_table(
        fit_data(eskd_numpy, table_width, ksize_font=ksize_font, delim=" "),
        header_table,
        table_width,
        rows_in_first_sheet,
        rows_in_other_sheet,
        start_possition,
        file_name,
        delta=25,
        align=align,
    )
    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )


# In[37]:


cord = total_length(G, devices, connected_contacts)
sleeve = sleeve_count(G, devices, connected_contacts)
cable_input = cable_input_count(outer_connection.cables_collection)
# equipment = {"Гильза": sleeve, "Провод": cord, "Гермоввод": cable_input}
equipment = {"Гильза": sleeve, "Провод": cord}

eskd_specification(su_device, cabine_definition, equipment)


# In[38]:


su_to_eskd(su_device, cabine_definition, equipment)


# In[39]:


device_specification(su_device)


# ### Вывод в Excel и в CSV для тестов

# In[40]:


safe_to_excel(
    device_specification(su_device, set_name=True),
    f"{plot_dir}/Спецификация устройств {WORK_CABINE}.xlsx",
    index=False,
)
safe_to_csv(
    device_specification(su_device, set_name=True),
    f"{output_dir}/Спецификация устройств {WORK_CABINE}-{unixtime}.csv",
    index=False,
)
safe_to_excel(
    pandas.DataFrame(enclosure_specification(cabine_definition, su_device, equipment)),
    f"{plot_dir}/Полная спецификация.xlsx",
    sheet_name="Спецификация",
    index=False,
)


# ### Чтение и загрузка ссылок в схему

# In[41]:


reference = read_reference_data(cabine_definition)


# In[42]:


reference


# In[43]:


reference_out = create_number_reference(reference, su_device)
reference_out


# In[44]:


safe_to_csv(
    reference_out,
    f"{plot_dir}/Загрузка инициализированных ссылок на спецификацию в чертеж Autocad {WORK_CABINE}.txt",
    sep="\t",
    encoding="cp1251",
    index=False,
)


# ## Общий скрипт печати соединения и подключения проводок, а также спецификации устройств

# In[45]:


AutocadElements(all_lisp_data).save(
    f"{plot_dir}/Общий скрипт соединения, подключения и спецификации {WORK_CABINE}.lsp"
)


# ## Печать графа объединяющего контакты устройств и короба

# In[46]:


from src.graph_view import GraphView


# In[47]:


cabine_montge = GraphView(contacts).plot(boxes, closet_graph, (3, 3))

AutocadElements(cabine_montge).save(
    f"{plot_dir}/Печать графа устройств {WORK_CABINE}.lsp"
)
_ = shutil.copyfile(
    f"{plot_dir}/Печать графа устройств {WORK_CABINE}.lsp",
    f"{output_dir}/Печать графа устройств {WORK_CABINE}-{unixtime}.lsp",
)


# # Отладка

# In[48]:


import unittest
from src.test import TestOutput


# In[49]:


TestOutput.UNIXTIME = unixtime
TestOutput.OUTPUT_DIR = output_dir
TestOutput.TEST_CASE = cabine_definition.test_case()
TestOutput.generate_tests()
_ = unittest.main(argv=[""], verbosity=1, exit=False)
