from sys import stderr

class NotFoundCable(Exception):
    pass

class DistanceZero(Exception):
    pass

class NotFoundHole(Exception):
    pass

class ReferenceToCableIncorect(Exception):
    pass

class TerminalIsBusy(Exception):
    pass

class CableIsBusy(Exception):
    pass

class IntersectionWires(Exception):
    def __init__(self, bad_clemmnics):
        for bc in bad_clemmnics:
            print(bc, bad_clemmnics[bc], file=stderr)
        super().__init__('Пересекающаяся проводка! Прежде чем двигаться дальше, исправь схему!')

class NotFoundDirection(Exception):
    pass

class CountUsedWiresModeCountWires(Exception):
    pass

class WireInCableAlreadyExist(Exception):
    def __init__(self, wire, cable, row):
        super().__init__(wire, cable, row, '''
Данная жила уже была добавлена в кабель!
Это возможно когда с одного шкафа в другой приходит одна и таже жила более одного раза на разные клеммники.
Например:
   Из ШУС в ЭКРУ дважды с Х5 уходит жила 701, первый раз она идет на Х1, а второй на Х2. И
   дополнительно из ШУС в ЭКРУ дважды с Х7 уходит жила 701, первый раз она идет на Х1,
   второй раз на Х2. Программы дважды жилу 701 из клеммники Х5 провидет на Х1 в ЭКРУ, а на Х2
   не проведет ни разу.
Теоретически жила должны была попасть в разные кабеля, но программа начинает занимать жилы
в массиве по порядку, и в итогде жила которая должна была уйти на разные кабеля попадает в один.
Если жила уже пришла в шкаф на клеммник, то не нужно ее туда отправлять второй раз, даже с другово клеммника.''')

class InvalideSectionOrCableType(Exception):
    pass

class NotKnowCable(Exception):
    pass

class NotFoundNeighbour(Exception):
    def __init__(self, center_contact, side):
        super().__init__(center_contact, side, '''
Для данного юнита (короб, контакт) небыло наудено парного юнита.
Возможно указано неверное напрявление в поле монтаж у контакта''')

class SingleContactForWire(Exception):
    def __init__(self):
        super().__init__('''
В схеме присутствуют жилы с одним контактом! Прежде чем двигаться дальше исправь их все!''')

class EmptyAndNotEmptyClemms(Exception):
    def __init__(self, bad_clemmnics):
        for el in bad_clemmnics:
            print(el[0], file=stderr)
            print(el[1], file=stderr)
        super().__init__( '''
В скемах есть проблеммные клеммники! На одном и томже клеммнике часть жил определены, а часть пустые!''')