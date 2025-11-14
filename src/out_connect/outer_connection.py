from src.out_connect.pandas import read_project_data
from src.out_connect.pandas import make_clemmnic_list
from src.out_connect.cable_connection import make_cable_connection
from src.out_connect.contact import make_contact_list
from src.out_connect.device import make_device_list


class OuterConnection:
    """
    В единый класс объединены вызовы методом постоения схемы внешних связей.
    """
    def __init__(self, station):
        self.project_data = read_project_data(station)
        self.clemmnic_data = make_clemmnic_list(self.project_data, station)
        self.cables_collection = make_cable_connection(self.clemmnic_data, station)
        self.contact_data = make_contact_list(self.project_data, station)
        self.device_data = make_device_list(self.project_data, station)

    def _get_attribute(self, cabin, contact_name, f_contact, f_clemmnic):
        result = f_contact(cabin, contact_name)
        if result is None:
            result = f_clemmnic(cabin, contact_name)
        return result

    def get_page(self, cabin, contact_name):
        page_contact = self.contact_data.page_contact
        page_clemmnic = self.clemmnic_data.page_clemmnic
        return self._get_attribute(cabin, contact_name, page_contact, page_clemmnic)

    def get_possition(self, cabin, contact_name):
        possition_contact = self.contact_data.possition_contact
        possition_clemmnic = self.clemmnic_data.possition_clemmnic
        return self._get_attribute(cabin, contact_name, possition_contact, possition_clemmnic)