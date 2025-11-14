from src.out_connect.cable import is_kvvg
from src.out_connect.cable import is_vvg
from src.out_connect.cable import get_diameter_kvvg
from src.out_connect.cable import get_diameter_vvg
from src.exception import NotFoundHole

def diameter_for_cabinet(cabinet, cables_collection):
    def calc_diameter(type_cab, num, section):
        def k_shield(s):
            return 1.15 if len(type_cab) >= len(s) and type_cab[0:len(s)] == s else 1

        result = 12
        if is_kvvg(type_cab):
            result = k_shield('КВВГЭ') * get_diameter_kvvg(int(num), float(section))
        elif is_vvg(type_cab):
            result = k_shield('ВВГЭ') * get_diameter_vvg(int(num), float(section))
        return int(result + 1.0)

    def accumulate_result(d):
        key = str(d)
        if key not in result:
            result[key] = 0
        result[key] += 1

    result = {}
    for cable in cables_collection.cables():
        if cabinet not in cables_collection.get_cabins_by_cable(cable):
            continue

        section, type_cab = cables_collection.section(cable)
        num = cables_collection.count_wires(cable)
        diameter = calc_diameter(type_cab, num, section)
        accumulate_result(diameter)

    preset_cables = cables_collection.station.preset_cables()
    for cable in preset_cables:
        if cabinet not in preset_cables.directions(cable):
            continue

        diameter = calc_diameter(
            preset_cables.get_type(cable),
            preset_cables.get_cores(cable),
            preset_cables.get_gauge(cable)
        )
        accumulate_result(diameter)

    return result


def calc_count_hole(cabinet, cables_collection):
    result = {}
    for d in diameter_for_cabinet(cabinet, cables_collection):
        M = {'16': [5, 9], '20': [8, 14], '25': [14, 18], '32': [18, 25], '40': [22, 32], '50': [25, 38], '60': [37, 44], '63': [40, 50]}
        search_success = False
        for m in M:
            if M[m][0] <= float(d) <= M[m][1]:
                if m not in result:
                    result[m] = 0
                result[m] += diameter_for_cabinet(cabinet, cables_collection)[d]
                search_success = True
                break
        if search_success == False:
            raise NotFoundHole(cabinet, d, 'Не найдент подходящий гермоввод под кабель!')

    return result