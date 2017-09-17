
# encoding: utf-8
from miniworld.model.singletons.Singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from .AbstractMovementPattern import AbstractMovementPattern
from random import randint


class WalkStub(AbstractMovementPattern):
    def __init__(self):
        super(WalkStub, self).__init__()

    def get_next_map_node(self, crt_map_node, last_map_node):
        list_of_next_pssible_roads = singletons.spatial_singleton.roads.get_list_of_next_roads_with_quality_restriction_for_cars(crt_map_node, 1)
        rand = randint(0, len(list_of_next_pssible_roads) - 1)
        return list_of_next_pssible_roads[rand]

    def get_speed(self):
        return randint(0, 5)
