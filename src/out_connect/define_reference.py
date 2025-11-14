import pandas
import yaml
from pathlib import Path

from src.yaml import cache_read_yaml_config
from src.station.misc import pairs_number_and_short_name


def search_clemma_in_contacts(contact_data, cabin, device, clemma):
    major, minor = ('', '')
    for contact in contact_data.get_list_contact_in_device(cabin, device):
        if contact.clemma == clemma:
            major, minor = contact.page.split(".")
            break
    return major, minor


def search_clemma_in_clemmnics(clemmnic_data, cabin, clemmnic, clemma):
    major, minor = ('', '')
    for contact in clemmnic_data:
        if contact.cabin == cabin and contact.clemmnic == clemmnic and contact.clemma == clemma:
            major, minor = contact.page.split(".")
            break
    return major, minor


def init_reference(station, contact_data, clemmnic_data):
    df = read_reference_for_set_page(station)
    result = []
    for _, row in df.iterrows():
        cabin, device, clemma = row['ID'].split(":")
        if cabin in pairs_number_and_short_name(station):
            cabin = pairs_number_and_short_name(station)[cabin]
        major, minor = search_clemma_in_contacts(contact_data, cabin, device, clemma)
        if major == '' and minor == '':
            major, minor = search_clemma_in_clemmnics(clemmnic_data, cabin, device, clemma)
        if major == '' and minor == '':
            raise Exception(cabin, device, clemma, "Не найден контакт в схеме!")

        a = {
            'HANDLE': row['HANDLE'],
            'BLOCKNAME': row['BLOCKNAME'],
            'ТЕКСТ': 'см.',
            'MAJOR': major,
            'MINOR': minor,
            'X': '',
            'Y': '',
            'ID': row['ID'],
        }
        result.append(a)
    return result


def read_reference_for_set_page(station):
    result = None
    match Path(station.scheme_file).suffix:
        case '.yaml': result = _read_yaml(station.scheme_file)
        case '.csv': result = _read_csv(station.scheme_file)
        case _: raise Exception(station.scheme_file, 'Не поддерживаемый формат данных!')
    return result

def _read_yaml(file_name):
    data = cache_read_yaml_config(file_name)
    result = []
    for d in data:
        if d['Real Name'] != 'REF':
            continue
        result.append({
            'HANDLE': f"'{d['Handle']}",
            'BLOCKNAME': d['Block Name'],
            'ТЕКСТ': 'см.',
            'MAJOR': d['Attribs']['MAJOR'],
            'MINOR': d['Attribs']['MINOR'],
            'X': d['Attribs']['X'],
            'Y': d['Attribs']['Y'],
            'ID': d['Attribs']['ID'],
        })
    return pandas.DataFrame(result)

def _read_csv(filename):
    return pandas.read_csv(filename, sep="\t", encoding="cp1251")