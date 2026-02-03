import os
from pathlib import Path
import hashlib
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def isNaN(num):
    return num != num


def eq(compare_value, float_num, eps=0.01):
    return ((float_num - eps <= compare_value) and (compare_value <= float_num + eps))


def md5(file_name):
    result = '00000000000000000000000000000000'
    if file_exist(file_name):
        hash_md5 = hashlib.md5()
        with open(file_name, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        result = hash_md5.hexdigest()
    return result


def check_test(prefix_name, unixtime, md5sum, output_dir):
    def check_md5sum(file, md5sum):
        return md5(f'{output_dir}/{file}') == md5sum

    my_file = f'{prefix_name}-{unixtime}'
    result_unix = []
    result_md5 = []

    for root, dirs, files in os.walk(output_dir, topdown=False):
        for file in files:
            if file[:len(prefix_name)] == prefix_name:
                if file[:len(my_file)] == my_file:
                    result_unix.append(file)
                if check_md5sum(file, md5sum):
                    result_md5.append(file)

    if len(result_unix) == 0 or len(result_md5) == 0:
        return 0

    last_md5 = result_md5[-1]
    ext_md5 = last_md5[-3:]
    result = []
    for file in result_unix:
        if ext_md5 == file[-3:]:
            result.append(f'vimdiff "{last_md5}" "{file}"')
    return result


def check_count_fields_in_csv(file_name, count):
    raise_exception = False
    with open(file_name, 'r') as f:
        for i, item in enumerate(f):
            if count != item.count(','):
                raise_exception = True
                print(i+1, item)
    if raise_exception:
        raise Exception('В данных присутствует лишняя запитая!')


def file_exist(file_name):
    return os.path.isfile(file_name)


def make_dir(path: Path):
    if not path.parent.exists():
        logger.info(f"Создаем директорию [{path.parent}] для файла [{path.name}]")
        path.parent.mkdir(parents=True, exist_ok=True)


def safe_open(file_path, *args, **kwargs):
    path = Path(file_path)
    make_dir(path)
    return path.open(*args, **kwargs)


def safe_to_csv(df: pd.DataFrame, path: str, **kwargs):
    make_dir(Path(path))
    df.to_csv(path, **kwargs)


def safe_to_excel(df: pd.DataFrame, path: str, **kwargs):
    make_dir(Path(path))
    df.to_excel(path, **kwargs)


def safe_excel_writer(path: str, **kwargs):
    make_dir(Path(path))
    return pd.ExcelWriter(path, **kwargs)


def my_str(s):
    result = str(s).strip()
    if result != str(s):
        logger.info(f'my_str: {result} != {str(s)}')
    return result