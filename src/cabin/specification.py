import pandas
from src.misc import isNaN as isNaN


def device_specification(su_device, set_name=False):
    def count_device():
        result = ''
        if device_info.unit == 'мм':
            result = str(device_info.count)
        elif device_info.unit == 'шт':
            result = str(device_info.name)
        return result
            
    result = []
    c = 1
    for device_info in sorted(su_device):
        a = {}
        a['Номер'] = 0
        a['Производитель'] = device_info.manufacture
        a['Описание'] = device_info.info
        a['Артикул'] = device_info.articul
        count = int(device_info.count)
        exist = False
        for i in result:
            if i['Производитель'] == a['Производитель'] and i['Описание'] == a['Описание'] and i['Артикул'] == a['Артикул']:
                if not isNaN(device_info.name):
                    i['Устройство'] = i['Устройство'] + ', ' + count_device()
                i['Кол-во'] += count
                exist = True
                break
        if exist == False:
            if isNaN(device_info.name):
                a['Устройство'] = ''
            else:
                a['Устройство'] = count_device()
            match device_info.typeplot:
                case '-1': a['Тип'] = '01'
                case '-2': a['Тип'] = '02'
                case '-3': a['Тип'] = '03'
                case _: a['Тип'] = '05' if str(device_info.name)[0] == 'X' or a['Устройство'] == '' else '06'

            a['Кол-во'] = count
            a['Ед'] = device_info.unit
            result.append(a)
            c += 1

    df = pandas.DataFrame(result).sort_values(by=['Тип', 'Ед', 'Производитель', 'Описание'], ignore_index=True)
    df['Номер'] = range(1, len(df['Номер'])+1)
    
    columns = list(df.columns)
    columns.remove('Тип')
    if set_name == False:
        columns.remove('Устройство')
        
    return pandas.DataFrame(df, columns=columns)


def su_to_eskd(su_device, cabine, equipment=False):
    df = device_specification(su_device, set_name=True)
    A3 = 'A3'
    A4 = 'A4'
    dk = 'ДОКУМЕНТАЦИЯ'
    sc = 'Спецификация'
    sb = 'Сборочный чертеж'
    sp = 'Соединения проводок'
    pp = 'Подключения проводок'
    ok = 'ОБОРУДОВАНИЕ И КОМПЛЕКТУЮЩИЕ ИЗДЕЛИЯ'
    st = 'л.'
    mt = 'МАТЕРИАЛЫ'
    sn = cabine.get_short_cabine_name()
    ln = cabine.get_long_cabine_name()
    blank_line =  {'Ф': '', 'З': '', 'П': '', 'Обозначение': '', 'Наименование': '', 'Кол': '', 'Примечание': ''}
    result = [
        blank_line,
        {'Ф': '', 'З': '', 'П': '', 'Обозначение': sn, 'Наименование': ln, 'Кол': 1,  'Примечание': ''},
        blank_line,
        {'Ф': '', 'З': '', 'П': '', 'Обозначение': '', 'Наименование': dk, 'Кол': '', 'Примечание': ''},
        {'Ф': A4, 'З': '', 'П': '', 'Обозначение': '', 'Наименование': sc, 'Кол': '', 'Примечание': st + ' 2'},
        {'Ф': A3, 'З': '', 'П': '', 'Обозначение': '', 'Наименование': sb, 'Кол': '', 'Примечание': st + ' 3'},
        {'Ф': A4, 'З': '', 'П': '', 'Обозначение': '', 'Наименование': sp, 'Кол': '', 'Примечание': st + ' 4'},
        {'Ф': A3, 'З': '', 'П': '', 'Обозначение': '', 'Наименование': pp, 'Кол': '', 'Примечание': st + ' 5'},
        blank_line,
        {'Ф': '', 'З': '', 'П': '', 'Обозначение': '', 'Наименование': ok, 'Кол': '', 'Примечание': ''}
    ]
    last_number = 0
    for _, row in df.iterrows():
        a = {}
        a['Ф'] = ''
        a['З'] = ''
        a['П'] = row['Номер']
        a['Обозначение'] = row['Устройство']
        a['Наименование'] = f'{row['Описание']}, {row['Производитель']}, (арт.:{row['Артикул']})' 
        a['Кол'] = row['Кол-во']
        a['Примечание'] = row['Ед']
        last_number = row['Номер']
        result.append(a)

    if equipment != False:
        number_equipment = last_number + 1
        result.append(blank_line)
        result.append({'Ф': '', 'З': '', 'П': '', 'Обозначение': '', 'Наименование': mt, 'Кол': '',  'Примечание': ''})
        for name_equipment, count_equipment in equipment.items():
            result.append(blank_line)
            for param in count_equipment.items():
                name, count, unit = get_equipment(name_equipment, param)
                result.append({'Ф': '', 'З': '', 'П': number_equipment, 'Обозначение': '', 'Наименование': name, 'Кол': count,  'Примечание': unit})
                number_equipment += 1

    return pandas.DataFrame(result)


def get_equipment(name, param):
    match name:
        case 'Провод':
            section, length = param
            result = (f'Провод монтажный {section} мм2', int(1+length/1000.0), 'м')
        case 'Гильза':
            sleeve, count = param
            result = (f'Втулочный наконечник НШВИ({sleeve[0]}): {sleeve}', count, 'шт')
        case 'Гермоввод':
            cable_input, count = param
            result = (f'Нейлоновый герметичный кабельный ввод с метрической резьбой: {cable_input}', count, 'шт')
        case _:
            raise Exception("Не определенный тип доп. материала!")
    return result


def enclosure_specification(cabine, su_device, equipment):
    def table_for_lilay(v1, v2, v3, v4, v5, v6):
        return {
            "Шкаф": v1,
            "Произв.": v2,
            "Арт": v3,
            "Название товара": v4,
            "Ед": v5,
            "Кол-во": v6,
            "Цена ед.": "",
            "Цена общ": "",
        }

    result = []
    cab_name = cabine.get_short_cabine_name()
    for _, row in device_specification(su_device, set_name=True).iterrows():
        result.append(table_for_lilay(
            cab_name,
            row["Производитель"],
            row["Артикул"],
            row["Описание"],
            row["Ед"],
            row["Кол-во"]
        ))
    
    if equipment != False:
        for name_equipment, count_equipment in equipment.items():
            for param in count_equipment.items():
                name, count, unit = get_equipment(name_equipment, param)
                result.append(table_for_lilay(
                    cab_name,
                    "",
                    "",
                    name,
                    unit,
                    count
                ))

    return result