from src.out_connect.direction import first_closet
from src.out_connect.direction import second_closet


def pprint(elements):
    COUNT = 7
    print('{', end='')
    for i, (key, val) in enumerate(elements.items(), start=1):
        print(f'"{key}": {val:4},', end=' ')
        if i % COUNT == 0:
            print('\n ', end='')
    print('}\n')

def AND(val1, val2):
    return val1 and val2

def OR(val1, val2):
    return val1 or val2

def _used_direction(cables_collection, func_distance, func_cabine, logic):
    list_direction = {}
    error_direction = set()
    
    for cable in cables_collection.cables():
        direction = cables_collection.cable_to_direction(cable)
        if direction not in list_direction:
            c1 = int(first_closet(direction))
            c2 = int(second_closet(direction))
            if logic(func_cabine(c1), func_cabine(c2)):
                if direction in func_distance():
                    list_direction[direction] = func_distance()[
                        direction
                    ]
                else:
                    error_direction.add(direction)
    if not error_direction:
        pprint(list_direction)
    else:
        print(error_direction)


def used_direction(station, cables_collection):
    _used_direction(cables_collection, cables_collection.distance_inside, station.is_inside, AND)
    _used_direction(cables_collection, cables_collection.distance_outside, station.is_outside, OR)


def what(element, what):
    if what == 'page':
        return element.page
    elif what == 'possition':
        return element.possition
    else:
        raise Exception(what, 'Для данного типа параметра значение не возвращается методом _what()!')