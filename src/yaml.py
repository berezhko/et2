import yaml
import numpy

from functools import cache


@cache
def cache_read_yaml_config(file_name):
    with open(file_name, encoding="cp1251") as stream:
        result = yaml.load(stream, Loader=yaml.CLoader)
    return result


def read_yaml_config(dtypes_main, dtypes_attribs, dtypes_properties, skip_keys, file_name):
    data = cache_read_yaml_config(file_name)
    dtypes = {'Attribs': dtypes_attribs, 'Properties': dtypes_properties}
    result = []
    for d in data:
        if d['Real Name'] in skip_keys:
            continue
        a = {}
        for key, (new_key, type_field) in dtypes_main.items():
            a[new_key] = type_field(d[key]) if key in d and d[key] else numpy.nan
        for parametr, dtype in dtypes.items():
            for key, (new_key, type_field) in dtype.items():
                a[new_key] = type_field(d[parametr][key]) if _check_value(d, parametr, key) else numpy.nan
        result.append(a)
    return result


def _check_value(d, parametr, key):
    return d[parametr] and key in d[parametr] and d[parametr][key]