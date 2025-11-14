from sys import stderr
from omegaconf import OmegaConf

from . import cabine_settings


class Cabine:
    def make_cabine(cabine, station, config_cabines):
        short_name = station.get_cabinet_list()[str(int(cabine))][0]
        config_cabines.cabine_num = cabine
        config_cabines.cabine_name = short_name
        cabine_config = OmegaConf.load(config_cabines.cabine_config)
        main_config = OmegaConf.load(config_cabines.main_config)
        config = OmegaConf.merge(config_cabines, main_config, cabine_config)
        config.station = station.STATION
        return Cabine(cabine, station, config)

    def __init__(self, cabine, station, config):
        self.conf = config
        self._cabine = cabine
        self._station = station
        self._number_str = str(int(cabine))
        self.READ_WIRES_FROM_FILE = config.wires_from_files
        self.READ_CLOSET_STRUCT_FROM_FILE = config.closet_struct_from_files
        self.closet_file = config.closet_file
        self.reference_file = config.reference_file
        self.specification = cabine_settings.read_specification_file(config)
        self.device_directory = config.device_dir
        self.conf = config

    def get_cabine_number(self):
        return self._cabine

    def get_long_cabine_name(self):
        return self._station.get_cabinet_list()[self._number_str][1]

    def get_short_cabine_name(self):
        return self._station.get_cabinet_list()[self._number_str][0]

    def get_ending_contact(self, wire):
        return cabine_settings.ending_contact(self.conf, wire)

    def is_one_contact_in_wire(self, wire, device, contact):
        return cabine_settings.is_one_contact_in_wire(self.conf, wire, device, contact)

    # Размер формата и начальная позиция для вывода схем "Подключения проводок"
    def wiring_connect_format(self):
        return cabine_settings.wiring_connect_format(self.conf)

    def get_type_wire(self, wire):
        return cabine_settings.get_type_wire(self.conf, wire)
        
    def get_count_clemms(self, clemmnic):
        return cabine_settings.get_count_clemms(self.conf, clemmnic)

    def get_clemmnic_direction(self, clemmnic):
        return cabine_settings.get_clemmnic_direction(self.conf, clemmnic)

    def test_case(self):
        return cabine_settings.test_case(self.conf)