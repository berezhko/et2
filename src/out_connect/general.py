import pandas
from collections import namedtuple

from src.station.misc import get_short_cabinet_name
from src.station.misc import get_long_cabinet_name
from src.out_connect.device import ViewDevice

import src.plot_table as pl
from src.plot_table import fit_data

from src.elements import Mtext
from src.elements import AutocadElements as AutocadElements


def make_cabinet_table(station):
    result = []
    for i, row in station.get_cabinet_list().items():
        a = {}
        a["Номер"] = i
        a["Обозначение"] = row[0]
        a["Наименование"] = row[1]
        state = "Существующий"
        if station.is_new(int(i)):
            state = "Новый"
        a["Примечание"] = state
        result.append(a)
    return sorted(result, key=lambda x: int(x["Номер"]))


def view_devices_with_contacts(station, contact_data, device_data, closet, devices=[], add_closet=False, add_blank_line=True):
    all_devices = [d.device for d in device_data.get_device(closet)]
    if not devices:
        devices = all_devices

    df = pandas.DataFrame()
    df_blank = pandas.DataFrame([ViewDevice.pandas_table('', '', '', '', '', '', '')])
    cabin = get_short_cabinet_name(station, int(closet))
    cabin_long = get_long_cabinet_name(station, int(closet))
    df_closet = pandas.DataFrame([ViewDevice.pandas_table('', '', cabin_long, '', '', '', '')])
    closet_added = False 
    view = ViewDevice(contact_data, device_data, closet)
    for device in sorted(devices):
        if device not in all_devices:
            continue
        view_device = view(device)
        df_view = pandas.DataFrame(
            view_device, index=range(1, len(view_device) + 1)
        ).fillna('-')
        if view_device:
            if add_closet and not closet_added:
                df = pandas.concat([df, df_blank]) if add_blank_line else df
                df = pandas.concat([df, df_closet])
                df = pandas.concat([df, df_blank]) if add_blank_line else df
                closet_added = True
            df = pandas.concat([df, df_view])
            df = pandas.concat([df, df_blank]) if add_blank_line else df
    if add_closet:
        df = pandas.concat([df, df_blank]) if add_blank_line else df
        df = pandas.concat([df, df_blank]) if add_blank_line else df
    return df


def device_list(station, contact_data, device_data):
    result = pandas.DataFrame()
    for closet in station.show_contacts_cabines():
        closet_device = view_devices_with_contacts(station, contact_data, device_data, closet, add_closet=True)
        result = pandas.concat([result, closet_device])
    return result


def print_work_scheme(station, file_name):
    config = station.conf.general_data.work_scheme
    start_x = config.start_possition.X
    start_y = config.start_possition.Y
    work_settings_file = station.settings_file
    work_scheme = pl.print_work_scheme(
        pandas.read_excel(
            work_settings_file,
            sheet_name='Рабочие чертежи',
            keep_default_na=False,
        ), 
        start_x,
        start_y,
        config.work_scheme,
    )
    link_scheme = pl.print_work_scheme(
        pandas.read_excel(
            work_settings_file,
            sheet_name='Ссылочные и прилагаемые',
            keep_default_na=False,
        ), 
        start_x + (config.sheet_width - sum(config.list_scheme.width)),
        start_y,
        config.list_scheme,
    )
    AutocadElements(work_scheme + link_scheme).save(file_name)


# ToDo в настоящий момент данная функция работает некорректно
# Появился блок "Лист" с атрибутом ЛИСТ, по данному блоку нужо
# вставлять надпись, а также расчитывать количество листов.
def print_schemes_name(station, file_name):
    config = station.conf.general_data.schemes_name
    start_x = config.start_possition.X
    start_y = config.start_possition.Y
    offset_y = config.offset_y if 'offset_y' in config else 0
    lisp = []
    for _, row in pandas.read_excel(
            station.settings_file,
            sheet_name='Рабочие чертежи',
            keep_default_na=False,
        ).iterrows():
        x = start_x
        y = start_y * (int(row['Лист']) - offset_y)
        # |(-120, 15)           |   
        # |             (-50, 0)| - Координы рамки в которую встанет имя листа
        lisp.append(
            Mtext((x - 120, y + 15), (x - 50, y), row['Наименование'], config.font_size, "_MC")
        )
    AutocadElements(lisp).save(file_name)


def save_cabinet_table(station, file_name):
    config = station.conf.general_data.cabine_list
    columns = ["Номер", "Обозначение", "Наименование", "Примечание"]
    table_width = config.table_width
    header_table = [columns]
    rows_in_table = config.rows_in_table
    start_possition = config.start_possition
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
        align=config.text_align,
    )
    pl.HEIGHT = height


def plot_devices(station, data_pandas, file_name):
    config = station.conf.general_data.devices_list
    pl.plot_split_table(
        fit_data(
            data_pandas.to_numpy(),
            config.table_width,
            ksize_font=len(config.table_width) * [config.k_size_font],
            delim=" ",
            add_blank_line=False,
        ),
        [list(data_pandas.columns)],
        config.table_width,
        config.rows_in_first_sheet,
        config.rows_in_other_sheet,
        config.start_possition,
        file_name,
        delta=config.delta,
        align=config.text_align,
    )