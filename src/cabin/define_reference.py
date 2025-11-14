import yaml
from yaml import CLoader
import numpy
from pathlib import Path
import pandas
import sys

from src.cabin.specification import device_specification
from src.yaml import cache_read_yaml_config


class FinderNumber:
    def __init__(self, su_device):
        self.su_device = device_specification(su_device)
        self.cache = self.init_cache()

    def init_cache(self):
        result = {}
        for _, row in self.su_device.iterrows():
            result[(row["Производитель"], row["Описание"], row["Артикул"])] = row["Номер"]
        return result

    def __call__(self, manuf, info, art):
        result = 0
        if (manuf, info, art) in self.cache:
            result = self.cache[(manuf, info, art)]
        return result


def create_number_reference(reference, su_device):
    reference_data = []
    zero_results = []
    _get_number_reference = FinderNumber(su_device)
    for index, row in reference.iterrows():
        a = {}
        a["HANDLE"] = row["HANDLE"]
        a["BLOCKNAME"] = row["BLOCKNAME"]
        a["НОМЕР"] = _get_number_reference(
            row["ПРОИЗВОДИТЕЛЬ"], row["ИНФОРМАЦИЯ"], row["АРТИКУЛ"]
        )
        a["ИНФОРМАЦИЯ"] = row["ИНФОРМАЦИЯ"]
        a["АРТИКУЛ"] = row["АРТИКУЛ"]
        a["ПРОИЗВОДИТЕЛЬ"] = row["ПРОИЗВОДИТЕЛЬ"]
        reference_data.append(a)
        if a["НОМЕР"] == 0:
            zero_results.append(a)
    if zero_results:
        for zero in zero_results:
            print(zero, file=sys.stderr)
        raise Exception('В спецификации не найдено устройство, проверь соответствие выносок и устройств!')
    return pandas.DataFrame(reference_data)


def read_reference_data(cabine_definition):
    result = None
    match Path(cabine_definition.closet_file).suffix:
        case '.yaml': result = _read_yaml(cabine_definition.closet_file)
        case '.csv': result = _read_csv(cabine_definition.reference_file)
    return result

def _read_yaml(file_name):
    data = cache_read_yaml_config(file_name)
    result = []
    for d in data:
        if d['Real Name'] != 'ВЫНОСКА':
            continue
        result.append({
            'HANDLE': f"'{d['Handle']}",
            'BLOCKNAME': d['Block Name'],
            'НОМЕР': numpy.nan,
            'ИНФОРМАЦИЯ': d['Attribs']['ИНФОРМАЦИЯ'],
            'АРТИКУЛ': d['Attribs']['АРТИКУЛ'],
            'ПРОИЗВОДИТЕЛЬ': d['Attribs']['ПРОИЗВОДИТЕЛЬ'],
        })
    return pandas.DataFrame(result)

def _read_csv(file_name):
    return pandas.read_csv(file_name, sep="\t", encoding="cp1251")