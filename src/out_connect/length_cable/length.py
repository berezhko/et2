import networkx
import pandas

from src.edge import make_edges
from src.station.misc import get_short_cabinet_name

from .pandas import make_boxes_list
from .pandas import make_cabine_list
from .pandas import read_cabines_data
from src.out_connect.direction import first_closet
from src.out_connect.direction import second_closet


class ClosetsGraph():
    global_edges = None
    def __init__(self, station):
        df = read_cabines_data(station)
        self.boxes = make_boxes_list(df)
        self.cabine = make_cabine_list(df)
        if self.__class__.global_edges is None:
            self.__class__.global_edges = make_edges(self.boxes, self.cabine, f'{station.OUTPUT_DIR}/length_global_edges.pickle', station.READ_LENGTH_FROM_FILE)
        self.closet_graph = networkx.Graph()
        self.closet_graph.add_weighted_edges_from(self.__class__.global_edges.weighted_edges())

    def get_length(self, node1, node2, weight='weight'):
        length = networkx.dijkstra_path_length(self.closet_graph, node1, node2, weight)
        return int((length + 1000)/1000.0)


class LengthCable():
    from typing import Dict
    _length: Dict = {}

    def __init__(self, station, cables_collection):
        self._station = station
        if not self.__class__._length:
            if self._station.CALC_LENGTH:
                closet_graph = ClosetsGraph(station)
                self.__class__._length = self._calc_length(cables_collection, closet_graph)
            else:
                self.__class__._length = {**self._station.distance_inside(), **self._station.distance_outside()}

    def _calc_length(self, cables_collection, closet_graph):
        result = {}
        for cable in cables_collection.cables():
            direction = cables_collection.cable_to_direction(cable)
            if direction in result:
                continue
            node1 = get_short_cabinet_name(self._station, int(first_closet(direction)))
            node2 = get_short_cabinet_name(self._station, int(second_closet(direction)))
            result[direction] = closet_graph.get_length(node1, node2)
        return result

    def distance_inside(self):
        result = {}
        for direction, length in self.__class__._length.items():
            if (
                self._station.is_inside(int(first_closet(direction))) and
                self._station.is_inside(int(second_closet(direction)))
            ):
                result[direction] = length
        return result

    def distance_outside(self):
        result = {}
        for direction, length in self.__class__._length.items():
            if (
                self._station.is_outside(int(first_closet(direction))) or
                self._station.is_outside(int(second_closet(direction)))
            ):
                result[direction] = length
        return result
