def add_zero(num: str|int) -> str:
    return '0'+ str(int(num)) if int(num) < 10 else str(num)

# Формируем словарь {'AE1': '01', .. 'АИИСКУЭ': '66'}
# для быстрого получения номера шкафа по его короткой абревиатуре
def pairs_number_and_short_name(station):
    result = {}
    cabinet_list = station.get_cabinet_list()
    for i in cabinet_list:
        num = add_zero(i)
        cabin = cabinet_list[i][0]
        result[cabin] = num
    return result


def get_long_cabinet_name(station, num):
    result = str(int(num))
    data = station.get_cabinet_list()
    if result in data.keys():
        return data[result][0] + ', ' + data[result][1]
    else:
        return result

    
def get_short_cabinet_name(station, num):
    result = str(int(num))
    data = station.get_cabinet_list()
    if result in data.keys():
        return data[result][0]
    else:
        return result
