from omegaconf import OmegaConf
from pathlib import Path

from src.station import station
from src.station import cabine

def load_config():
    project_dir = Path(__file__).resolve().parent.parent.parent
    station = OmegaConf.load(project_dir / "config/station.yaml")
    config = OmegaConf.load(project_dir / "config/config.yaml")
    #conf_main = OmegaConf.merge(station, config)

    config.station = station.station
    config.project_dir = project_dir
    config.settings_yaml = config.settings_dir + station.settings_yaml
    config.settings_file = config.settings_dir + station.settings_xlsx
    config.scheme_file = config.scheme_dir + station.scheme_file
    config.cable_layout_file = ''
    if 'cable_layout_file' in station:
        config.cable_layout_file = config.scheme_dir + station.cable_layout_file
    conf_station = OmegaConf.load(config.settings_yaml)
    return OmegaConf.merge(config, conf_station)

def get_station():
    conf = load_config()
    return station.Station(conf, cabine.Cabine)

def get_default_cabin():
    conf = load_config()
    return conf.cabines.default_cabine
