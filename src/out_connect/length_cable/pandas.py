import pandas
from pathlib import Path

from src.out_connect.pandas import remove_elements_from_layer
from src.misc import check_count_fields_in_csv
from src.yaml import read_yaml_config

from .cabine import Cabine
from .box3d import Box3DList
from .box3d import Box3D


def make_boxes_list(df):
    df = remove_elements_from_layer(df, 'Шкафы')

    pandas_box = df[df['Имя'] == 'КОРОБ']
    result = Box3DList()
    sorted_data = pandas_box.sort_values(by=['Положение Y', 'Положение X', 'Положение Z'])
    i = 0
    for _, row in sorted_data.iterrows():
        X = row['Положение X']
        Y = row['Положение Y']
        Z = row['Положение Z']
        x = row['X']
        y = row['Y']
        z = row['Z']
        
        c = (X + x/2, Y + y/2, Z + z/2)
        l = (c[0] - x/2, c[1], c[2])
        r = (c[0] + x/2, c[1], c[2])
        f = (c[0], c[1] - y/2, c[2])
        R = (c[0], c[1] + y/2, c[2])
        d = (c[0], c[1], c[2] - z/2)
        u = (c[0], c[1], c[2] + z/2)
        box = Box3D(c, l, r, f, R, d, u, i)
        result.append(box)
        i = i + 1
    return result


def make_cabine_list(df):
    pandas_cabine = df[df['Имя'] == 'ШКАФ']
    result = []
    sorted_data = pandas_cabine.sort_values(by=['Положение Y', 'Положение X', 'Положение Z'])
    i = 0
    for _, row in sorted_data.iterrows():
        X = row['Положение X']
        Y = row['Положение Y']
        Z = row['Положение Z']
        n = row['ИМЯ1']
        d = row['МОНТАЖ']
        N = str(int(row['НОМЕР']))
        c = (X, Y, Z)

        result.append(Cabine(n, N, d, c))
        i = i + 1
    return result


def read_cabines_data(station):
    match Path(station.CABINE_FILE).suffix:
        case '.csv': df = read_cabines_csv_data(station.CABINE_FILE)
        case '.yaml': df = read_cabines_yaml_data(station.CABINE_FILE)
        case _: raise Exception(station.CABINE_FILE, 'Не поддерживаемый формат данных!')
    return df.sort_values(by=['Имя', 'Положение X', 'Положение Y', 'Положение Z'])

def read_cabines_csv_data(file_name):
    dtype = {
        'Имя': str,
        'Положение X': float,
        'Положение Y': float,
        'Положение Z': float,
        'X': float,
        'Y': float,
        'Z': float,
        'ИМЯ1': str,
        'МОНТАЖ': str,
        'НОМЕР': str,
        'Поворот': float,
        'Слой': str,
    }
    check_count_fields_in_csv(file_name, len(dtype)-1)
    return pandas.read_csv(file_name, dtype=dtype)

def read_cabines_yaml_data(file_name):
    dtypes_main = {
        'Real Name': ('Имя', str),
        'Layer': ('Слой', str),
        'X': ('Положение X', float),
        'Y': ('Положение Y', float),
        'Z': ('Положение Z', float),
    }
    dtypes_attribs = {
        'ИМЯ_ТРАССЫ': ('ИМЯ_ТРАССЫ', str),
        'ИМЯ': ('ИМЯ1', str),
        'МОНТАЖ': ('МОНТАЖ', str),
        'НОМЕР': ('НОМЕР', str),
    }
    dtypes_properties = {
        'X': ('X', float),
        'Y': ('Y', float),
        'Z': ('Z', float),
    }
    skip_blocks = ()

    result = read_yaml_config(dtypes_main, dtypes_attribs, dtypes_properties, skip_blocks, file_name)
    return pandas.DataFrame(result)
