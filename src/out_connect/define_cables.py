import yaml
from yaml import CLoader
import numpy
from pathlib import Path
import pandas

from src.yaml import cache_read_yaml_config
from src.exception import NotFoundCable
from src.station.misc import pairs_number_and_short_name
from .direction import make_direction
from .direction import is_direction

def read_cables_for_set_name(station):
    result = None
    match Path(station.scheme_file).suffix:
        case '.yaml': result = _read_yaml(station.scheme_file)
        case '.csv': result = _read_csv(station.cable_set_file)
    return result

def _read_yaml(file_name):
    data = cache_read_yaml_config(file_name)
    result = []
    for d in data:
        if d['Real Name'] != 'КАБЕЛЬ3':
            continue
        result.append({
            'HANDLE': f"'{d['Handle']}",
            'BLOCKNAME': d['Block Name'],
            'КАБЕЛЬ': numpy.nan,
            'КЛЕММНИК1': d['Attribs']['КЛЕММНИК1'],
            'КЛЕММНИК2': d['Attribs']['КЛЕММНИК2'],
            'НАПРАВЛЕНИЕ': d['Attribs']['НАПРАВЛЕНИЕ'],
        })
    return pandas.DataFrame(result)

def _read_csv(file_name):
    return pandas.read_csv(file_name, sep="\t", encoding="cp1251")

class DefineCable():
    def __init__(self, station):
        self._station = station

    def _separate_by_colon(self, string):
        pos = string.find(":")
        return (string[0:pos], string[pos+1:-1]+string[-1])
    
    def _get_number_cabin(self, cabin_and_terminal):
        cabine = self._get_cabine(cabin_and_terminal)
        result = 0
        if cabine.isnumeric():
            result = cabine
        if cabine in pairs_number_and_short_name(self._station).keys():
            result = pairs_number_and_short_name(self._station)[cabine]
        return result

    def _get_cabine(self, cabin_and_terminal):
        return self._separate_by_colon(cabin_and_terminal)[0]

    def _get_terminal_block(self, cabin_and_terminal):
        return self._separate_by_colon(cabin_and_terminal)[1]

    def make_direction(self, cabin_and_terminal1, cabin_and_terminal2):
        cab1 = self._get_number_cabin(cabin_and_terminal1)
        tb1 = self._get_terminal_block(cabin_and_terminal1)
        
        cab2 = self._get_number_cabin(cabin_and_terminal2)
        tb2 = self._get_terminal_block(cabin_and_terminal2)
        
        if int(cab1) > int(cab2):
            cab1, cab2, tb1, tb2 = cab2, cab1, tb2, tb1
        return (make_direction(cab1, cab2), tb1, tb2)

def set_cable_name(station, cables_collection):
    cables = read_cables_for_set_name(station)
    result = []
    def_cable = DefineCable(station)
    for _, row in cables.iterrows():
        direction, tb1, tb2 = def_cable.make_direction(row['КЛЕММНИК1'], row['КЛЕММНИК2'])
        if direction == row['НАПРАВЛЕНИЕ']:
            full_direction = f"{direction}:{tb1}:{tb2}"
            cable = cables_collection.find_cable_by_direction(full_direction)
            if cable == 0:
                cable = row['НАПРАВЛЕНИЕ']
                raise NotFoundCable(cable, row, "Кабель не найден в структуре cables_collection. Возможно 'Блок КАБЕЛЬ3' не согласован с клеммами, которые он объединяте. Перегинерируйте 'Блок КАБЕЛЬ3'.")
        else:
            cable = row['НАПРАВЛЕНИЕ']
            print(direction, " != ", row['НАПРАВЛЕНИЕ'])
        result.append({
            'HANDLE': row['HANDLE'],
            'BLOCKNAME': row['BLOCKNAME'],
            'КАБЕЛЬ': cable,
            'КЛЕММНИК1': row['КЛЕММНИК1'],
            'КЛЕММНИК2': row['КЛЕММНИК2'],
            'НАПРАВЛЕНИЕ': row['НАПРАВЛЕНИЕ'],
        })
    return result

def get_cable_without_names(cables_data):
    "Не назначенные кабеля"
    cable_without_names = pandas.DataFrame()
    for row in cables_data:
        if is_direction(row["КАБЕЛЬ"]):
            cable_without_names = pandas.concat(
                [cable_without_names, pandas.Series(row).to_frame().T]
            )
    return cable_without_names

def get_cable_with_name_equal_direction(cables_data):
    df = pandas.DataFrame(cables_data)
    if df.empty:
        return df
    else:
        return df[df["КАБЕЛЬ"] == df["НАПРАВЛЕНИЕ"]].sort_values(by=["КАБЕЛЬ"])
