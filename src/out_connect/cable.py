# Match all, begining "КВВГ" (КВВГнг, КВВГЭ, КВВГЭнг, КВВГЭнг(A)-LS, etc)
def is_kvvg(type_cab):
    return type_cab[0:4] == 'КВВГ'


def is_vvg(type_cab):
    return type_cab[0:3] == 'ВВГ'


def is_utp(type_cab):
    return (type_cab.find('UTP') != -1) or (type_cab.find('FTP') != -1) or (type_cab.find('STP') != -1)


def get_diameter_kvvg(num, float_section):
    kvvg = {"1.0": {4: 8.5, 5: 10, 7: 11, 10: 13, 14: 14, 19: 15, 27: 18, 37: 20, 52: 24, 61: 25}, 
            "1.5": {4: 10,  5: 11, 7: 11, 10: 14, 14: 15, 19: 16, 27: 20, 37: 22, 52: 26, 61: 28}, 
            "2.5": {4: 11,  5: 12, 7: 12, 10: 15, 14: 17, 19: 18, 27: 22, 37: 25}, 
            "4.0": {4: 12,         7: 15, 10: 18}, 
            "6.0": {4: 14,         7: 16, 10: 21}}
    section = str(float_section)

    if section not in kvvg.keys():
        raise Exception(num, section, 'Ошибка поиска сечение для данного типа КВВГ кабеля!')
    if num not in kvvg[section].keys():
        raise Exception(num, section, 'Ошибка поиска диаметра для данного количества жил!')

    return kvvg[section][num]


def get_diameter_vvg(num, float_section):
    vvg = {"1x1.5": 5.4, "1x2.5": 5.8, "1x4.0": 6.6, "1x6.0": 7.1, "1x10.0": 8.0, "1x16.0": 10.1, "1x25.0": 11.2, 
           "1x35.0": 12.2, "1x50.0": 13.7, "1x70.0": 15.2, "1x95.0": 17.3, "1x120": 19.2, "1x150.0": 22.2, "1x185": 24.7, 
           "1x240": 27.7, "1x300": 31.0, "2x1.5": 8.4, "2x2.5": 9.7, "2x4.0": 11.5, "2x6.0": 12.5, "2x10.0": 14.1, 
           "2x16.0": 16.7, "2x25.0": 19.8, "2x35.0": 21.8, "2x50.0": 25.2, "2x70.0": 28.2, "2x95.0": 32.4, "2x120": 35.8, 
           "2x150": 41.8, "3x1.5": 9.5, "3x2.5": 10.3, "3x4.0": 12.1, "3x6.0": 13.2, "3x10.0": 14.9, "3x16.0": 17.8, 
           "3x25.0": 21.0, "3x35.0": 23.2, "3x50.0": 26.8, "3x150.0": 38, "4x1.5": 10.2, "4x2.5": 11.1, "4x4.0": 13.2, "4x6.0": 14.4, 
           "4x10.0": 16.4, "4x16.0": 20.4, "4x25.0": 23.2, "4x35.0": 26.0, "4x50.0": 29.6, "4x150.0": 42.6, "5x1.5": 11.1, "5x2.5": 12.1, 
           "5x4.0": 14.5, "5x6.0": 15.8, "5x10.0": 18.0, "5x16.0": 22.5, "5x25.0": 25.9, "5x35.0": 28.6, "5x50.0": 32.7, 
           "5x70.0": 38.0, "5x95.0": 42.2, "5x120": 45.7, "5x150": 49.5, "5x185": 53.6, "5x240": 60.1}

    key = str(num) + 'x' + str(float_section)
    if key not in vvg.keys():
        raise Exception(num, float_section, 'Ошибка поиска сечение для данного типа ВВГ кабеля!')

    return int(vvg[key]+1)


def get_kvvg(num, float_section) -> str:
    section = str(float_section)
    kvvg = {}
    kvvg['1.0'] = [4, 5, 7, 10, 14, 19, 27, 37, 52, 61]
    kvvg['1.5'] = [4, 5, 7, 10, 14, 19, 27, 37, 52, 61]
    kvvg['2.5'] = [4, 5, 7, 10, 14, 19, 27, 37]
    kvvg['4.0'] = [4, 7, 10]
    kvvg['6.0'] = [4, 7, 10]
    
    if num < 16:
        temp = num*1.2
    else:
        temp = num*1.1

    result = 0
    for k in kvvg[section]:
        if temp < k:
            result = str(k)
            break

    if result == 0:
        raise Exception(num, section, 'Для данного сечение не найден подходящий кабель!')

    return result


def get_vvg(num, float_section) -> str:
    section = str(float_section)
    vvg_section = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

    if num < 5:
        temp = num+1
    elif num == 5:
        temp = num
    else:
        raise Exception(num, 'Кабеля ВВГ с данным количеством жил не существует!')

    return str(temp)


def get_utp(num, float_section) -> str:
    return str(8)
