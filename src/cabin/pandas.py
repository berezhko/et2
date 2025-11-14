import pandas
import os.path
from pathlib import Path

from dataclasses import dataclass, field
from typing import Union, List, Tuple, Dict

from src.misc import check_count_fields_in_csv
from src.yaml import read_yaml_config

from .specification_unit import SpecificationUnitList
from .specification_unit import SpecificationUnit
from .specification_unit import AutocadTemplate

from .contact import Contact
from .contact import ConnectedContact
from .contact import ConnectedContactList

from .box import BoxList
from .box import Box


def make_su_device_list(closet_file, specification):
    df = read_cabine_data(closet_file)
    pandas_block = df[df["Имя"] == "БЛОК"]

    result = create_su_device(pandas_block)
    if not specification.empty:
        for spec_unit in create_su_device(specification):
            result.append(spec_unit)
    return result


def create_su_device(pandas_block):
    result = SpecificationUnitList()
    for i, row in pandas_block.iterrows():
        match row['КОЛИЧЕСТВО1']:
            case 'Высота':
                count = str(int(row['Высота']))
                unit = 'мм'
            case 'Ширина':
                count = str(int(row['Ширина']))
                unit = 'мм'
            case _:
                count = str(int(row['КОЛИЧЕСТВО1']))
                unit = 'шт'

        d = SpecificationUnit(
            row['ПРОИЗВОДИТЕЛЬ'],
            row['ИНФОРМАЦИЯ'],
            row['АРТИКУЛ'],
            count,
            unit,
            row['ИМЯ1'],
            int(row['РЯД']),
            (10**6)*int(row['Положение X']) - int(row['Положение Y']),
            str(row['ТИП'])
        )
        result.append(d)
    return result


def make_contacts_list(closet_file):
    df = read_cabine_data(closet_file)
    pandas_contact = df[df["Имя"] == "КОНТАКТ"]

    result = []
    for index, row in pandas_contact.iterrows():
        contact = Contact(
            row['НОМЕР'],
            row['ИМЯ1'],
            (row['Положение X'], row['Положение Y']),
            row['МОНТАЖ'],
        )
        result.append(contact)
    return result


def make_boxes_list(closet_file):
    df = read_cabine_data(closet_file)
    pandas_box = df[df["Имя"] == "КОРОБ"]

    result = BoxList()
    sorted_data = pandas_box.sort_values(by=['Положение Y', 'Положение X'])
    i = 0
    for _, row in sorted_data.iterrows():
        X = row['Положение X']
        Y = row['Положение Y']
        c = (X, Y)
        l = (X - row['Ширина']/2, Y)
        r = (X + row['Ширина']/2, Y)
        d = (X, Y - row['Высота']/2)
        u = (X, Y + row['Высота']/2)
        box = Box(c, l, r, d, u, i)
        result.append(box)
        i = i + 1
    return result


def make_connected_contact_list(pandas_clemma, pandas_clemma_outside):
    def make_connected_contact_list(df, type_device):
        result = ConnectedContactList()
        for _, clemma in df.iterrows():
            result.append(
                ConnectedContact(
                    clemma[type_device],
                    clemma['ВН_ЖИЛА'],
                    float(clemma['СЕЧЕНИЕ']),
                    str(clemma['КЛЕММА']),
                    type_device,
                )
            )    
        return result

    result = make_connected_contact_list(pandas_clemma, 'УСТРОЙСТВО')
    result += make_connected_contact_list(pandas_clemma_outside, 'КЛЕММНИК')

    return result


def read_cabine_data(closet_file):
    match Path(closet_file).suffix:
        case '.csv': df = read_cabine_csv_data(closet_file)
        case '.yaml': df = read_cabine_yaml_data(closet_file)
        case _: raise Exception(closet_file, 'Не поддерживаемый формат данных!')
    return df.sort_values(by=['Имя', 'Положение X', 'Положение Y'])

def read_cabine_yaml_data(file_name):
    dtypes_main = {
        'Real Name': ('Имя', str),
        'X': ('Положение X', float),
        'Y': ('Положение Y', float),
    }
    dtypes_attribs = {
        'КОЛИЧЕСТВО': ('КОЛИЧЕСТВО1', str),
        'ИНФОРМАЦИЯ': ('ИНФОРМАЦИЯ', str),
        'АРТИКУЛ': ('АРТИКУЛ', str),
        'ИМЯ': ('ИМЯ1', str),
        'ПРОИЗВОДИТЕЛЬ': ('ПРОИЗВОДИТЕЛЬ', str),
        'РЯД': ('РЯД', str),
        'ТИП': ('ТИП', str),
        'МОНТАЖ': ('МОНТАЖ', str),
        'НОМЕР': ('НОМЕР', str),
    }
    dtypes_properties = {
        'Высота': ('Высота', float),
        'Ширина': ('Ширина', float),
    }
    skip_blocks = ('ВЫНОСКА')

    result = read_yaml_config(dtypes_main, dtypes_attribs, dtypes_properties, skip_blocks, file_name)
    return pandas.DataFrame(result)


def read_cabine_csv_data(closet_file):
    dtype = {
        "Количество": 'int64',
        "Имя": str,
        "АРТИКУЛ": str,
        "Высота": 'float64',
        "ИМЯ1": str,
        "ИНФОРМАЦИЯ": str,
        "КОЛИЧЕСТВО1": str,
        "Положение X": 'float64',
        "Положение Y": 'float64',
        "ПРОИЗВОДИТЕЛЬ": str,
        "РЯД": str,
        "ТИП": str,
        "Ширина": 'float64',
        "МОНТАЖ": str,
        "НОМЕР": str,
    }
    check_count_fields_in_csv(closet_file, len(dtype)-1)
    return pandas.read_csv(closet_file, dtype=dtype)


def read_contacts_template_data(template_name):
    contacts_sheet_name = "Contacts"
    contacts_dtype = {
        "Контакт": str,
        "Положение X": int,
        "Положение Y": int,
    }
    contacts = None
    if contacts_sheet_name in pandas.ExcelFile(template_name).sheet_names:
        contacts = pandas.read_excel(
            template_name,
            sheet_name=contacts_sheet_name,
            dtype=contacts_dtype,
            keep_default_na=False
        )
    return contacts

def read_geometry_template_data(template_name):
    geometry_sheet_name = "Geometry"
    geometry_dtype = {
        "РазмерБлока X": int,
        "РазмерБлока Y": int,
        "ПоворотБлока": int,
    }
    geometry = None
    if geometry_sheet_name in pandas.ExcelFile(template_name).sheet_names:
        geometry = pandas.read_excel(
            template_name,
            sheet_name=geometry_sheet_name,
            dtype=geometry_dtype,
            keep_default_na=False
        )
    return geometry


def read_autocad_template(template_name):
    contacts_df = read_contacts_template_data(template_name)
    geometry_df = read_geometry_template_data(template_name)

    contacts = {}
    for a in contacts_df.to_dict('records'):
        contacts[a['Контакт']] = (a['Положение X'], a['Положение Y'])

    geometry = {}
    for a in geometry_df.to_dict('records'):
        geometry['РазмерБлока X'] = a['РазмерБлока X']
        geometry['РазмерБлока Y'] = a['РазмерБлока Y']
        geometry['ПоворотБлока'] = a['ПоворотБлока']
        break  # Считается, что устройство представляется только одним блоком
    
    return (contacts, geometry)


def get_autocad_template_path(template_dir, device_type):
    return template_dir + device_type + '.xlsx'


def make_autocad_template(template_dir, device_type):
    template_name = get_autocad_template_path(template_dir, device_type)
    contacts, geometry = read_autocad_template(template_name)
    return AutocadTemplate(device_type, contacts, geometry['РазмерБлока X'])
