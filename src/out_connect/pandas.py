import pandas
from pathlib import Path

from src.station.misc import pairs_number_and_short_name
from src.misc import check_count_fields_in_csv
from src.exception import IntersectionWires

from src.out_connect.page_number import page_number
from src.out_connect.clemmnic import ClemmnicList
from src.out_connect.clemmnic import Clemmnic
from src.out_connect.clemmnic import check_intersection_clemmnic

from src.misc import safe_to_excel
from src.misc import my_str
from src.yaml import read_yaml_config


# Не работаем со Слоем 'Дублированные блоки'
def remove_elements_from_layer(df, layer):
     return df[df['Слой'] != layer]


# В файле выгруженом из Autocad замняем текстовые названия шкафов на их цифровые значения
def rename_cabin_name_to_number(df, station):
    short_names = pairs_number_and_short_name(station)
    for cabin in short_names:
        num = short_names[cabin]
        # Закоментировано, так как давала ворнинг на обновленном окружении.
        # Необходимо протестировать на полном проекте и удалить если операции равнозначные!
        #df['ШКАФ'].mask(df['ШКАФ'] == cabin, num, inplace=True)
        df['ШКАФ'] = df['ШКАФ'].replace(cabin, num)
    return df


# Выбираем данные с не пустым значением колонки 'КЛЕММНИК'
def get_clemmnic_data(df):
    no_points_nans = df[~df['КЛЕММНИК'].isna()]
    return pandas.DataFrame(no_points_nans, columns=['КЛЕММА', 'ШКАФ', 'ЖИЛА', 'КАБЕЛЬ', 'ВН_ЖИЛА', 'КЛЕММНИК', 'СЕЧЕНИЕ', 'ТИП_КАБЕЛЯ', 'Положение X', 'Положение Y'])


# Выбираем данные с не пустым значением колонки 'КАБЕЛЬ2', и заменяем колонку КАБЕЛЬ2 на КАБЕЛЬ
def get_clemmnic_with_cabel2_data(df):
    no_points_nans = df[~df['КАБЕЛЬ2'].isna()]
    df = pandas.DataFrame(no_points_nans, columns=['КЛЕММА', 'ШКАФ', 'ЖИЛА', 'КАБЕЛЬ2', 'ВН_ЖИЛА', 'КЛЕММНИК', 'СЕЧЕНИЕ', 'ТИП_КАБЕЛЯ', 'Положение X', 'Положение Y'])
    return df.rename(columns={"КАБЕЛЬ2": "КАБЕЛЬ"})


def make_device_list(df, station):
    pdm = df
    pdm = pdm[(pdm['Имя'] == 'Устройство') & (~pdm['ШКАФ'].isna())].sort_values(by=['ШКАФ', 'УСТРОЙСТВО'])
    columns = ['УСТРОЙСТВО', 'ШКАФ', 'ТИП', 'Положение X', 'Положение Y', 'ЛИСТ', 'Тип1', 'ПРИМЕЧАНИЕ', 'Слой']
    for new_column in ['АРТИКУЛ', 'ПРОИЗВОДИТЕЛЬ']:
        if new_column in df.keys():
           columns += [new_column]
    pdm = pandas.DataFrame(pdm, columns=columns)
    pdm['ЛИСТ'] = ''
    for index, row in pdm.iterrows():
        pdm.loc[index, 'ЛИСТ'] = page_number(station, row['Положение X'], row['Положение Y'])
    return pdm


def make_reference_list(df, station):
    pdm = df
    pdm = pdm[pdm['Имя'] == 'REF']
    pdm = pandas.DataFrame(pdm, columns=['ID', 'MAJOR', 'MINOR', 'ТЕКСТ', 'X', 'Y', 'Положение X', 'Положение Y', 'ЛИСТ'])
    pdm['ЛИСТ'] = ''
    for index, row in pdm.iterrows():
        pdm.loc[index, 'ЛИСТ'] = page_number(station, row['Положение X'], row['Положение Y'])
    return pdm


def make_contact(row):
    return (
        row['ШКАФ'],
        row['УСТРОЙСТВО'],
        row['КЛЕММА'],
        row['ВН_ЖИЛА'],
        row['СЕЧЕНИЕ'],
        (row['Положение X'], row['Положение Y']),
        row['ЛИСТ'],
    )


def make_contact_list(df, station):
    pdm = df
    pdm = pdm[((pdm['Имя'] == 'КЛЕММА_ВН2') | (pdm['Имя'] == 'КЛЕММА_ВН1')) & (pdm['ВН_ЖИЛА'] != '-')]
    pdm = pandas.DataFrame(pdm, columns=['ВН_ЖИЛА', 'КЛЕММА', 'УСТРОЙСТВО', 'ШКАФ', 'СЕЧЕНИЕ', 'Положение X', 'Положение Y', 'ЛИСТ'])
    pdm['ЛИСТ'] = ''
    for index, row in pdm.iterrows():
        pdm.loc[index, 'ЛИСТ'] = page_number(station, row['Положение X'], row['Положение Y'])
    return pdm


def make_clemmnic_list(df, station, raise_exception=True):
    result = ClemmnicList(station)
    sorted_data = join_single_and_double_clemmnic(df).sort_values(by=['ШКАФ', 'КЛЕММНИК', 'КЛЕММА'])
    
    def init_virtual_clemmnic(clemmnic, cabin):
        return init_clemmnic(cabin, clemmnic, station.get_virtual_clemmnic())

    def init_real_clemmnic(clemmnic, cabin):
        return init_clemmnic(cabin, clemmnic, station.get_real_clemmnic())
    
    def init_clemmnic(cabin, clemmnic, clemmnics):
        result = clemmnic
        if cabin in clemmnics:
            for true_clemmnic, union_clemmnics in clemmnics[cabin].items():
                if clemmnic in union_clemmnics:
                    result = true_clemmnic
                    break
        return result
        
    for index, row in sorted_data.iterrows():
        number = 0
        direction = row['КАБЕЛЬ']
        page = page_number(station, row['Положение X'], row['Положение Y'])
        clemmnic = Clemmnic(row['ШКАФ'],
                            row['КЛЕММНИК'],
                            init_virtual_clemmnic(row['КЛЕММНИК'], row['ШКАФ']),
                            init_real_clemmnic(row['КЛЕММНИК'], row['ШКАФ']),
                            row['КЛЕММА'],
                            row['ЖИЛА'],
                            row['ВН_ЖИЛА'],
                            direction,
                            number,
                            row['КАБЕЛЬ'],
                            row['ТИП_КАБЕЛЯ'],
                            row['СЕЧЕНИЕ'],
                            row['ОБРАБОТАНО'],
                            (row['Положение X'], row['Положение Y']),
                            page)
        result.append(clemmnic)

    intersection_clemmnic = check_intersection_clemmnic(result)
    if raise_exception == True and intersection_clemmnic != {}:
        raise IntersectionWires(intersection_clemmnic)
    return result


def join_single_and_double_clemmnic(df):
    df1 = get_clemmnic_data(df)
    df2 = get_clemmnic_with_cabel2_data(df)
    result = pandas.concat([df1, df2], ignore_index=False, sort=False)
    result = result.reset_index()
    result = get_clemmnic_data(result)
    result["ОБРАБОТАНО"] = 0
    return result


# Используются в программе Шкафы make_list_wires


def get_inner_clemma(df, closet):
    pandas_clemma = df[(df['ШКАФ'] == closet) & ((df['Имя'] == 'КЛЕММА_ВН2') | (df['Имя'] == 'КЛЕММА_ВН1'))]
    return pandas_clemma[~pandas_clemma['ВН_ЖИЛА'].isna()]


def get_outer_clemma(df, closet):
    pandas_clemma_outside = df[(df['ШКАФ'] == closet) & ((df['Имя'] == 'КЛЕММА1') | (df['Имя'] == 'КЛЕММА2') | (df['Имя'] == 'КЛЕММА1_2КАБ') | (df['Имя'] == 'КЛЕММА2_2КАБ'))]
    return pandas_clemma_outside[~pandas_clemma_outside['ВН_ЖИЛА'].isna()]

def read_project_data(station):
    match Path(station.scheme_file).suffix:
        case '.csv': df = read_project_csv_data(station.scheme_file)
        case '.yaml': df = read_project_yaml_data(station.scheme_file)
        case _: raise Exception(station.scheme_file, 'Не поддерживаемый формат данных!')
    df = df.sort_values(by=['ШКАФ', 'Имя', 'КЛЕММНИК', 'УСТРОЙСТВО', 'КЛЕММА'])
    number_cabin = rename_cabin_name_to_number(df, station)
    return remove_elements_from_layer(number_cabin, "Дублированные блоки")

def read_project_csv_data(file_name):
    dtype = {
        'Имя': str,
        'ВН_ЖИЛА': str,
        'КЛЕММА': str,
        'УСТРОЙСТВО': str,
        'ШКАФ': str,
        'ЖИЛА': str,
        'КАБЕЛЬ': str,
        'КЛЕММНИК': str,
        'КАБЕЛЬ2': str,
        'ЖИЛА2': str,
        'ТИП': str,
        'Тип1': str,
        'СЕЧЕНИЕ': 'float64',
        'ТИП_КАБЕЛЯ': str,
        'Слой': str,
        'Положение X': 'float64',
        'Положение Y': 'float64',
        'ПРИМЕЧАНИЕ': str,
    }
    check_count_fields_in_csv(file_name, len(dtype)-1)
    return pandas.read_csv(file_name, dtype=dtype)

def read_project_yaml_data(file_name):
    dtypes_main = {
        'Real Name': ('Имя', my_str),
        'Layer': ('Слой', my_str),
        'X': ('Положение X', float),
        'Y': ('Положение Y', float),
    }
    dtypes_attribs = {
        'ВН_ЖИЛА': ('ВН_ЖИЛА', my_str),
        'КЛЕММА': ('КЛЕММА', my_str),
        'УСТРОЙСТВО': ('УСТРОЙСТВО', my_str),
        'ШКАФ': ('ШКАФ', my_str),
        'ЖИЛА': ('ЖИЛА', my_str),
        'КАБЕЛЬ': ('КАБЕЛЬ', my_str),
        'КЛЕММНИК': ('КЛЕММНИК', my_str),
        'КАБЕЛЬ2': ('КАБЕЛЬ2', my_str),
        'ЖИЛА2': ('ЖИЛА2', my_str),
        'ТИП': ('ТИП', my_str),
        'СЕЧЕНИЕ': ('СЕЧЕНИЕ', float),
        'ТИП_КАБЕЛЯ': ('ТИП_КАБЕЛЯ', my_str),
        'ПРИМЕЧАНИЕ': ('ПРИМЕЧАНИЕ', my_str),
        'АРТИКУЛ': ('АРТИКУЛ', my_str),
        'ПРОИЗВОДИТЕЛЬ': ('ПРОИЗВОДИТЕЛЬ', my_str),
    }
    dtypes_properties = {
        'Тип': ('Тип1', my_str),
    }
    skip_blocks = ('REF', 'КАБЕЛЬ3')

    result = read_yaml_config(dtypes_main, dtypes_attribs, dtypes_properties, skip_blocks, file_name)
    return pandas.DataFrame(result)


def used_wires(contact_data, clemmnic_data, file_name):
    sort_list = ['cabin', 'inner_wire']
    df = pandas.DataFrame(contact_data)
    res = df[(df['cabin'] != '') & (df['inner_wire'] != '')].sort_values(sort_list)
    df1 = pandas.DataFrame(res, columns=['cabin', 'device', 'clemma', 'inner_wire', 'page'])
    
    df = pandas.DataFrame(clemmnic_data)
    res = df[(df['cabin'] != '') & (df['inner_wire'] != '')].sort_values(sort_list)
    res = pandas.DataFrame(res, columns=['cabin', 'clemmnic', 'clemma', 'inner_wire', 'page'])
    df2 = res.rename(columns={"clemmnic": "device"})
    
    safe_to_excel(pandas.concat([df1, df2]).sort_values(sort_list), file_name, index=False)
    