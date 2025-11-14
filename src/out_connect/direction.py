def is_direction(direction):
    return direction[0] == '#'


# direction предполагается как #0106
def first_closet(direction):
    return direction[1:3]


# direction предполагается как #0106
def second_closet(direction):
    return direction[3:5]


# direction предполагается как #0106
def get_cabins_by_direction(direction):
    return [first_closet(direction), second_closet(direction)]


# По НАПРАВЛЕНИЕ и названию одного из шкафов получем номер второго шкафа
def get_back_cabinet_from_direction(cabinet, direction):
    result = -1
    if cabinet ==  first_closet(direction):
        result = second_closet(direction)
    elif cabinet == second_closet(direction):
        result =  first_closet(direction)

    if result == -1:
        raise Exception(cabinet, direction, "Шкаф не указан в НАПРАВЛЕНИЕ")
    return result

def make_direction(first_cabin: str, second_cabin: str) -> str:
    if int(first_cabin) > int(second_cabin):
        raise Exception(first_cabin, second_cabin, "Номер первого шкафа больше номера второго шкафа!")
    return '#' + first_cabin + second_cabin