#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas
import shutil

from omegaconf import OmegaConf
from pathlib import Path
from os.path import basename
from datetime import datetime


# In[2]:


unixtime = round(datetime.now().timestamp())


# In[3]:


from src.station import config


# In[4]:


project_config = config.load_config()


# In[5]:


ekra_config = OmegaConf.load(
    project_config.project_dir / "config" / project_config.station / "ekra.yaml"
)


# In[6]:


project_config = OmegaConf.merge(project_config, ekra_config)


# In[7]:


output_dir = project_config.outp_dir
plot_dir = project_config.plot_dir
ekra_setpoint = project_config.EKRA_FILE
nrows_sp = project_config.EKRA_ROWS
ekra_skip_protection = project_config.EKRA_SKIP_PROTECTION


# In[8]:


import src.plot_table as pl
from src.plot_table import fit_data


# In[9]:


pandas.set_option("display.max_rows", None)


# In[10]:


def replace_utf8(data_numpy):
    table_replace = {"Δ": "d", "≡": "m"}
    result = []
    for row in data_numpy:
        a = []
        for string in row:
            for what_replace, them_replace in table_replace.items():
                if string.find(what_replace) != -1:
                    string = string.replace(what_replace, them_replace)
            a.append(string)
        result.append(a)
    return result


def add_blank_line(data_numpy):
    result = []
    for i, row in enumerate(data_numpy):
        a = []
        if row[0] != "" and i != 0:
            result.append(len(row) * [""])
            print(f" ({row[0]})")
        for string in row:
            a.append(string)
        result.append(a)
    return result


def skip_protection(data_numpy):
    result = []
    skip = False
    for i, row in enumerate(data_numpy):
        a = []
        protection_name = row[0]
        if protection_name != "":  # Нашли начало уставок новой защиты
            skip = False
            for protection in ekra_skip_protection:  # Проверяем, нужно ли ее пропустить
                if protection_name.find(protection) != -1:
                    skip = True
                    break
            print(f'{"-" if skip else " "}[{protection_name}]: {i}')
        if skip == True:
            continue

        for string in row:
            a.append(string)
        result.append(a)
    return result


# In[11]:


def plot_setpoints_protect(data_pandas, file_name):
    rows_in_first_sheet = 52
    rows_in_other_sheet = 62
    start_possition = {"X": 20, "Y": -13}
    table_width = [18, 15, 12, 10, 5, 5, 60, 20, 10, 15, 15]
    ksize_font = len(table_width) * [3.2 / 5]
    align = ["l", "c", "c", "c", "c", "l", "l", "l", "c", "c", "c"]
    if len(table_width) != len(align):
        raise Exception("Различное кол-во эл. в таблицах table_width и align")

    data_numpy = data_pandas.to_numpy()
    data_numpy = skip_protection(data_numpy)
    data_numpy = replace_utf8(data_numpy)
    data_numpy = add_blank_line(data_numpy)
    header_table = [list(range(1, len(table_width) + 1))]

    pl.plot_split_table(
        fit_data(
            data_numpy,
            table_width,
            ksize_font=ksize_font,
            delim=" ",
            add_blank_line=False,
        ),
        header_table,
        table_width,
        rows_in_first_sheet,
        rows_in_other_sheet,
        start_possition,
        file_name,
        delta=25,
        align=align,
    )

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )


# In[12]:


usecols_sp = [5, 0, 1, 2, 3, 4, 6, 10, 11, 15, 16]
dtype = str

setpoint = pandas.read_excel(
    ekra_setpoint,
    skiprows=lambda x: True if x < 5 else False,
    sheet_name="Бланк уставок",
    keep_default_na=False,
    header=None,
    usecols=usecols_sp,
    nrows=nrows_sp,
    dtype=dtype,
)


# In[13]:


plot_setpoints_protect(setpoint[usecols_sp], f"{plot_dir}/Схемы/РЗ. Уставки защит.lsp")


# In[14]:


pandas.set_option("display.max_columns", 25)


# In[15]:


def plot_matrix_breaker(data_pandas, file_name):
    rows_in_first_sheet = 44
    rows_in_other_sheet = 64
    start_possition = {"X": 20, "Y": -350}
    table_width = [55, 50] + 20 * [4]
    ksize_font = len(table_width) * [3.2 / 5]
    align = ["l", "l"] + 20 * ["c"]
    if len(table_width) != len(align):
        raise Exception("Различное кол-во эл. в таблицах table_width и align")

    data_numpy = data_pandas.to_numpy()
    data_numpy = replace_utf8(data_numpy)
    header_table = [list(range(1, len(table_width) + 1))]

    pl.plot_split_table(
        fit_data(
            data_numpy,
            table_width,
            ksize_font=ksize_font,
            delim=" ",
            add_blank_line=False,
        ),
        header_table,
        table_width,
        rows_in_first_sheet,
        rows_in_other_sheet,
        start_possition,
        file_name,
        delta=25,
        align=align,
    )

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )


# In[16]:


usecols_mb = list(range(2, 24))
matrix_breaker = pandas.read_excel(
    ekra_setpoint,
    sheet_name="Матрица",
    skiprows=4,
    header=None,
    usecols=usecols_mb,
    keep_default_na=False,
    dtype=str,
)


# In[17]:


plot_matrix_breaker(matrix_breaker, f"{plot_dir}/Схемы/РЗ. Матрица отключений.lsp")


# In[18]:


matrix_breaker


# In[19]:


setpoint[usecols_sp]
