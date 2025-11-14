from dataclasses import dataclass, field
from typing import Union, List, Tuple, Dict
from scipy.spatial.distance import cdist
from scipy.spatial.distance import minkowski
import numpy as np

from .cabin.contact import Contact
from .cabin.box import Box
from .out_connect.length_cable.cabine import Cabine
from .out_connect.length_cable.box3d import Box3D

import pickle


def calc_distance(p1, p2):
    return int(minkowski(p1, p2, 2))


@dataclass
class Edge():
    node1: Union[Box, Contact, Box3D, Cabine]
    node2: Union[Box, Contact, Box3D, Cabine]
    distance: float


class EdgeList(List[Edge]):
    def __init__(self, boxes, contacts):
        self._boxes = boxes
        self._build_edge(boxes, lambda d: min(1, d.min()))  # Так как я сам себе сосед, то ограничивая мин 1, я не добавляю цеклические ребра
        self._build_edge(contacts, lambda d: d.min())


    # Определяем соседнюю к нам ячейку (берем только одного соседа)
    def _find_neighbour(self, a, b, index, min_func):
        result = None
        dist = cdist(np.array([a]), np.array(b), metric='minkowski', p=2)
        dist_min = min_func(dist)
        
        for j, d in enumerate(dist[0]):
            if d <= dist_min:
                result = self._boxes[index[j]]
                break
        return result
    
    
    # Генерируем список ребер
    def _build_edge(self, units, min_func):
        for unit in units:
            for side in unit.available_direction():
                a = unit.get_coordinate(side)
                b, index = self._boxes.array_with_suitable_boxs(unit.center, unit.s(side))
                neighbour = self._find_neighbour(a, b, index, min_func)
                if neighbour is None:
                    continue
                distance = calc_distance(unit.center, neighbour.center)
                if distance == 0:
                    raise ValueError(unit.full_name, neighbour.full_name, 'distance == 0!')
                self.append(Edge(unit, neighbour, distance))


    def weighted_edges(self):
        result = []
        for edge in self:
            result.append((edge.node1.full_name, edge.node2.full_name, edge.distance))
        return result


def make_edges(boxes, contacts, pikle_edges_file, load_from_file):
    result = None
    if load_from_file:
        with open(pikle_edges_file, "rb") as file:
            result = pickle.load(file)
    else:
        result = EdgeList(boxes, contacts)
        with open(pikle_edges_file, "wb") as file:
            pickle.dump(result, file)
    return result
