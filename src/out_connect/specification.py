import pandas
import numpy
from src.misc import safe_to_csv
from src.misc import safe_to_excel
from src.misc import safe_excel_writer
from collections import Counter
from collections import defaultdict

import logging

logger = logging.getLogger(__name__)

from src.out_connect.cable_journal import total_length_journal
from src.plot_table import fit_data
import src.plot_table as pl
from src.station.misc import get_short_cabinet_name
from src.station.misc import get_long_cabinet_name


def cable_to_specification(station, cables_collection):
    result = [['N', 'Кабельная продукция', '', '', '', '', '', '', '']]
    for type_cable, length in total_length_journal(station, cables_collection).items():
        result.append(['', ' '.join(type_cable), '', '', '', 'м', length, '', ''])
    result.append(['-', '', '', '', '', '', '', '', ''])
    return numpy.array(result)


def all_equipment(station, clemmnic_data, get_list_devices):
    result = [['-', '', '', '', '', '', '', '', '']]
    for cabin in clemmnic_data.get_list_cabine():    
        if cabin in station.develop_cabins():
            continue
        info = {}
        already_added = defaultdict(set)
        for dev in get_list_devices(cabin):
            name = f"{dev.full_info} {dev.art}"
            if name in info:
                info[name][4] += dev.count
                if not dev.device in already_added[name]:
                    info[name][5] += f", {dev.device}"
                    already_added[name].add(dev.device)
                else:
                    if not dev.is_clemmnic():
                        logger.warning(f"Шкаф: '{cabin}'. Устойство '{dev.device}' добавляется в спецификацию повторно.")
            else:
                info[name] = [dev.art, dev.order_num, dev.manuf, dev.unit, dev.count, dev.device]
                already_added[name].add(dev.device)
    
        if not info:
            continue
        a = ['N', f"{get_long_cabinet_name(station, int(cabin))} ({get_short_cabinet_name(station, int(cabin))})", '', '', '', '', '', '', '']
        result.append(a)
        for name, value in info.items():
            a = ['', name, value[0], value[1], value[2], value[3], value[4], '', value[5]]
            result.append(a)
        result.append(['-', '', '', '', '', '', '', '', ''])
        
    return result


def set_number_possition(spds_array):
    num_major = 0
    num_minor = 1
    for row in spds_array:
        if row[0] == '':
            if num_major == 0:
                num_major = 1
            row[0] = f'{num_major}.{num_minor}'
            num_minor += 1
        elif row[0] == 'N':
            num_major += 1
            num_minor = 1
            row[0] = f'{num_major}'
        elif row[0] == '-':
            row[0] = ''
    return spds_array


def spds_specification_array(station, cables_collection, clemmnic_data, get_list_devices):
    spds_cable = cable_to_specification(station, cables_collection)
    spds_equipment = station.get_specification()

    other_equipment = all_equipment(station, clemmnic_data, get_list_devices)
    result = numpy.concatenate((spds_cable, spds_equipment, other_equipment), axis=0)
    set_number_possition(result)

    return result


def spds_specification_excel(spds_array, output_file, copy_to_csv=False):
    header = [
        "Поз.",
        "Наименование и техническая характеристика",
        "Тип, марка, обозначение документа, опросного листа",
        "Код продукции",
        "Поставщик",
        "Ед. измерения",
        "Количество",
        "Масса 1 ед., кг",
        "Примечание",
    ]
    spds_excel = pandas.DataFrame(spds_array, columns=header)
    safe_to_excel(spds_excel, output_file, sheet_name="Спецификация", index=False)
    
    if copy_to_csv:
        spds_csv = pandas.DataFrame(spds_excel, columns=header[1:])
        safe_to_csv(spds_csv, output_file[:-4]+"csv", sep=";", index=False)
    

def spds_specification(spds_array, output_file, config):
    height = pl.HEIGHT
    pl.HEIGHT = config.height
    pl.plot_split_table(
        fit_data(
            spds_array,
            config.table_width,
            ksize_font=len(config.table_width)*[config.k_size_font],
            delim=' '),
        [list(config.header)],
        config.table_width,
        config.rows_in_first_sheet,
        config.rows_in_other_sheet,
        config.start_possition,
        output_file,
        delta=config.delta,
        align=config.text_align
    )
    pl.HEIGHT = height


def get_list_devices_in_closet(closet, device_data):
    '''
    Список устройств в шкафу. Пропускаются только контакты реле
    и Слой "Не учитывать в спецификации"
    '''
    result = []
    for dev in device_data.get_device_for_spec(
        closet
    ):  
        result.append(dev)
    return result


def summary_equipment_schedule(station, clemmnic_data, device_data):
    '''
    Информация о количестве типов устройств в спецификации.
    А также Итоговое количество.
    Необходима для более удобной работы закупщиков.
    '''
    result_cabin = defaultdict(list)
    result = []
    for cabine in clemmnic_data.get_list_cabine():
        for device in get_list_devices_in_closet(cabine, device_data):
            if device:
                dev = ', '.join([device.man_art, device.info])
                result_cabin[get_short_cabinet_name(station, cabine)].append(dev)
                result.append(dev)
    return {c: dict(Counter(r)) for c, r in result_cabin.items()} | {'Итого': Counter(result)}


def used_devices_for_specification(station, closets, device_data, file_name):
    '''
    Таблица устройств в спецификации. Необходима для более удобной работы закупщиков.
    '''
    with safe_excel_writer(file_name) as writer:
        for closet in closets:
            devices = get_list_devices_in_closet(closet, device_data)
            if devices:
                devices_arr = [[dev.cabin, dev.device, dev.man_art, dev.info] for dev in devices]
                devices_df = pandas.DataFrame(
                    devices_arr, columns=["ШКАФ", "УСТРОЙСТВО", "ТИП", "ПРИМЕЧАНИЕ"]
                ).sort_values(by=["УСТРОЙСТВО", "ТИП", "ПРИМЕЧАНИЕ"])
                cabin = get_short_cabinet_name(station, int(closet))
                devices_df.to_excel(writer, sheet_name=cabin, index=False)


def create_device_config(device, file_path):
    '''
    Создание шаблона устройства.
    '''
    file_name = f'{file_path}{device.man_art}.xlsx'
    with safe_excel_writer(file_name) as writer:
        contacts = pandas.DataFrame(
            columns=['Номер', 'Монтаж', 'Положение X', 'Положение Y']
        )
        device = {
            'Производитель': device.manuf,
            'Артикул': device.true_art,
            'Информация': device.full_info,
            'Количество': 1,
            'Видимость': 1,
            'Строка': 1,
            'Тип': '-',
            'Положение X': 0,
            'Положение Y': 0,
            'Смещение': 2
        }
        device = pandas.DataFrame(device, index=[1],
            columns=['Производитель', 'Артикул', 'Информация', 'Количество', 'Видимость', 'Строка', 'Тип', 'Положение X', 'Положение Y', 'Ширина', 'Высота', 'Смещение']
        )
        contacts.to_excel(writer, sheet_name='Contacts', index=False)
        device.to_excel(writer, sheet_name='Devices', index=False)

def generate_equipment_config(clemmnic_data, device_data, output_path):
    '''
    Создание шаблонов устройств. Используются для генерации БЛОКов в чертежах ЗЗИ.
    '''
    device_created = set()
    for cabine in clemmnic_data.get_list_cabine():
        for device in get_list_devices_in_closet(cabine, device_data):
            if device and device.art not in device_created:
                create_device_config(device, output_path)
                device_created.add(device.art)