import pandas
import os.path


def read_specification_file(config):
    sheet_name = "Спецификация"
    result = pandas.DataFrame()
    if os.path.exists(config.settings):
        if sheet_name in pandas.ExcelFile(config.settings).sheet_names:
            result = pandas.read_excel(config.settings, sheet_name=sheet_name, keep_default_na=False)
    return result


def ending_contact(config, wire):
    result = []
    if 'ending_contacts' in config:
        if wire in config.ending_contacts:
            result = config.ending_contacts[wire]
    return result


def is_one_contact_in_wire(config, wire, device, contact):
    result = False
    if 'one_contact' in config:
        if [wire, device, contact] in config.one_contact:
            result = True
    return result


def get_type_wire(config, wire):
    special_type = {}
    if 'type_wires' in config:
        special_type = config.type_wires

    result = config.default_type_wires
    for type_wire, wires in special_type.items():
        if wire in wires:
            result = type_wire
            break
    return result


# Параметры для вывода схем "Подключения проводок"
def wiring_connect_format(config):
    return config.wiring_connect_format


def _get_clemmnic_params(config, clemmnic, index):
    result = None
    if 'clemmnic_params' in config:
        if clemmnic in config.clemmnic_params:
            result = config.clemmnic_params[clemmnic][index]
    return result

def get_clemmnic_direction(config, clemmnic):
    result = _get_clemmnic_params(config, clemmnic, 1)
    if result is None:
        result = config.default_clemmnic_direction
    return result

def get_count_clemms(config, clemmnic):
    result = _get_clemmnic_params(config, clemmnic, 0)
    if result is None:
        result = config.default_count_clemms
    return result

def test_case(config):
    return config.tests
