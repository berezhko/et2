import pandas
from collections import namedtuple

from src.station.misc import get_short_cabinet_name
from src.station.misc import get_long_cabinet_name
from src.out_connect.device import ViewDevice

import src.plot_table as pl
from src.plot_table import fit_data

from src.elements import Mtext
from src.elements import AutocadElements as AutocadElements


TableParams = namedtuple('TableParams', 'height rows_count width align')


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


def get_something(df, x, y, table_param, header=True):
    start_possition = {"X": x, "Y": y}
    ksize_font = len(list(df.columns)) * [(4 / table_param.height) * 3.2 / 5]
    if header:
        header_table = [list(df.columns)]
    else:
        header_table = None
    data_numpy = df.to_numpy()

    pl.HEIGHT = table_param.height
    result = pl.get_split_table(
        fit_data(
            data_numpy,
            table_param.width,
            ksize_font=ksize_font,
            delim=" ",
            add_blank_line=False
        ),
        header_table,
        table_param.width,
        table_param.rows_count,
        table_param.rows_count,
        start_possition,
        delta=5,
        align=table_param.align,
    )
    pl.HEIGHT = 4
    return result


def print_work_scheme(station, file_name, start_x, start_y):
    work_settings_file = station.settings_file
    work_scheme_table = TableParams(
        6, 24,
        [15, 140, 30],
        ["c", "l", "l"],
    )
    link_scheme_table = TableParams(
        6, 37,
        [60, 95, 30],
        ["l", "l", "l"],
    )
    sheet_width = 395

    work_scheme = get_something(
        pandas.read_excel(
            work_settings_file,
            sheet_name='Рабочие чертежи',
            keep_default_na=False,
        ), 
        start_x,
        start_y,
        work_scheme_table,
    )

    link_scheme = get_something(
        pandas.read_excel(
            work_settings_file,
            sheet_name='Ссылочные и прилагаемые',
            keep_default_na=False,
        ), 
        start_x + (sheet_width - sum(link_scheme_table.width)),
        start_y,
        link_scheme_table,
    )

    AutocadElements(work_scheme + link_scheme).save(file_name)


def print_schemes_name(station, file_name, start_x, start_y, offset_y=0):
    lisp = []
    for _, row in pandas.read_excel(
            station.settings_file,
            sheet_name='Рабочие чертежи',
            keep_default_na=False,
        ).iterrows():
        x = start_x
        y = start_y * (int(row['Лист']) - offset_y)
        p1 = (x - 120, y + 15)
        p2 = (x - 50, y)
        lisp.append(
            Mtext(p1, p2, row['Наименование'], 3, "_MC")
        )
    AutocadElements(lisp).save(file_name)