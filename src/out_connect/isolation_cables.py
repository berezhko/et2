import random
import src.out_connect.montage_cable as montage_cable
from src.out_connect.cable import is_kvvg, is_vvg

class Isolation:
    def __init__(self, station, cables_collection, contact_data, clemmnic_data, generate_r=False):
        self.station = station
        self.cables_collection = cables_collection
        self.contact_data = contact_data
        self.clemmnic_data = clemmnic_data
        self.generate_r = generate_r
        montage_cable.station = station
        montage_cable.cables_collection = cables_collection
        montage_cable.contact_data = contact_data
        montage_cable.clemmnic_data = clemmnic_data
        self._clemmnics = self._init_clemmnics()

    def _get_cables(self, cell, clemma):
        result = []
        for y in cell.Y:
            result.append(montage_cable.get_cable(y))
        return result

    def _init_clemmnics(self):
        result = []
        for _, cells_cabin in montage_cable.calc_montage_data(self.clemmnic_data.get_list_cabine(), frame=montage_cable.AA).items():
            for cell in cells_cabin:
                for i in range(cell.count_clemms()):
                    clemma = self.station.get_clemma(cell.first+i, cell.cabin, cell.clemmnic)
                    wire_outside, _ = montage_cable.get_wire_and_device(cell, clemma)
                    for cable in self._get_cables(cell, clemma):
                        a = {}
                        a["Кабель"] = cable
                        a["Жила"] = wire_outside
                        a["Шкаф"] = cell.cabin
                        a["Клеммник"] = cell.clemmnic
                        a["Клемма"] = clemma
                        result.append(a)
        return result

    def _find_clemmnic(self, cable, wire, cabine):
        result = None
        for d in self._clemmnics:
            if d["Кабель"] == cable and d["Жила"] == wire and d["Шкаф"]:
                result = (d["Клеммник"], d["Клемма"])
                break
        return result

    def _make(self, c, w, c1, cl1, clm1, c2, cl2, clm2):
        before = random.randrange(10, 150)
        after = before + random.randrange(-3, 10)
        a = {}
        a['Кабель'] = c
        a['Жила'] = w
        a['Шкаф 1'] = c1
        a['Клеммник 1'] = cl1
        a['Клемма 1'] = clm2
        a['Шкаф 2'] = c2
        a['Клеммник 2'] = cl2
        a['Клемма 2'] = clm2
        a['R из. до испытаний'] = str(before) if self.generate_r else ''
        a['1000В 50Гц 1мин'] = '+'
        a['R из. после испытаний'] = str(after) if self.generate_r else ''
        return a

    def __call__(self):
        result = []
        for cable in self.cables_collection.cables():
            section, type_cab = self.cables_collection.section(cable)
            if not is_kvvg(type_cab) and not is_vvg(type_cab):
                continue
            count_wires_in_cab = int(self.cables_collection.count_wires(cable))
            for wire in self.cables_collection.wires(cable):
                cabine1 = self.cables_collection.get_cabins_by_cable(cable)[0]
                cabine2 = self.cables_collection.get_cabins_by_cable(cable)[1]
                cl1, clm1 = self._find_clemmnic(cable, wire, cabine1)
                cl2, clm2 = self._find_clemmnic(cable, wire, cabine2)
                a = self._make(
                    cable,
                    wire,
                    self.station.get_cabine_name(cabine1).short,
                    cl1,
                    clm1,
                    self.station.get_cabine_name(cabine2).short,
                    cl2,
                    clm2,
                )
                result.append(a)
                count_wires_in_cab -= 1
            for i in range(count_wires_in_cab):
                cabine1 = self.cables_collection.get_cabins_by_cable(cable)[0]
                cabine2 = self.cables_collection.get_cabins_by_cable(cable)[1]
                a = self._make(
                    cable,
                    'Резерв',
                    self.station.get_cabine_name(cabine1).short,
                    '',
                    '',
                    self.station.get_cabine_name(cabine2).short,
                    '',
                    '',
                )
                result.append(a)
        return result