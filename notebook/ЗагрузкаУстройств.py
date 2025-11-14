#!/usr/bin/env python
# coding: utf-8

# # Программа подготавливающая скрипт загрузки блоков устройств в схему Шкафа

# ## Подключение проектируемого объекта и функций проекта

# In[1]:


from collections import namedtuple
from os.path import basename
from datetime import datetime
import shutil
from pprint import pprint
import logging
import os


# In[2]:


from src.logging_config import setup_logging

app_name = "ЗагрузкаУстройств"
setup_logging(app_name)

logger = logging.getLogger(__name__)
logger.info(f"Запуск приложения: {app_name}")
logging.getLogger("src.cabin.upload_device").setLevel(logging.DEBUG)


# In[3]:


from src.station import config

station = config.get_station()


# In[4]:


CABIN = config.get_default_cabin()
cabine_definition = station.get_cabine_data(CABIN)
WORK_CABINE = cabine_definition.get_cabine_number()
device_dir = cabine_definition.device_directory
unixtime = round(datetime.now().timestamp())


# In[5]:


plot_dir = station.PLOT_DIR
output_dir = station.OUTPUT_DIR


# In[6]:


from src.misc import md5


# In[7]:


from src.out_connect import montage_cable
from src.out_connect.outer_connection import OuterConnection


# In[8]:


from src.cabin import upload_device
from src.cabin.upload_device import get_near_jumper
from src.lisp_template import insert_device_with_contacts

upload_device.CABIN = CABIN
upload_device.device_directory = device_dir


# In[9]:


def save(file_name, lisp):
    from src.cabin.upload_device import lisp_main

    with open(file_name, "w+", encoding="cp1251") as f:
        f.write(insert_device_with_contacts(lisp))

    _ = shutil.copyfile(
        file_name, f"{output_dir}/{basename(file_name)[:-4]}-{unixtime}.lsp"
    )
    return md5(file_name)


# ## Чтение исходной схемы и инициализация основных структур

# In[10]:


outer_connection = OuterConnection(station)


# In[11]:


montage_cable.station = station
montage_cable.contact_data = outer_connection.contact_data
montage_cable.clemmnic_data = outer_connection.clemmnic_data
montage_cable.cables_collection = outer_connection.cables_collection


# In[12]:


save(
    f"{plot_dir}/Шкаф/{WORK_CABINE}/build_clemmnic {WORK_CABINE}.lsp",
    upload_device.insert_clemmnic_with_contacts(
        outer_connection.device_data, montage_cable
    ),
)


# In[13]:


# assert md5(f'{plot_dir}/Шкаф/{WORK_CABINE}/build_clemmnic {WORK_CABINE}.lsp') == 'bc1950574a2fe49fa3db0fbc08d64d7a'


# ## Подготовка скрипта lisp вставляющего блоки устройст в схему

# In[14]:


save(
    f"{plot_dir}/Шкаф/{WORK_CABINE}/build_device {WORK_CABINE}.lsp",
    upload_device.insert_device_with_contacts(outer_connection.device_data),
)


# In[15]:


# assert md5(f'{plot_dir}/Шкаф/{WORK_CABINE}/build_device {WORK_CABINE}.lsp' == 'ef96d238dc7fca37fa2728b51a2e4c3a'
