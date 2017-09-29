# encoding: utf-8
from miniworld.model.singletons.Singletons import singletons

from random import randint

from .AbstractMovementPattern import AbstractMovementPattern

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class MoveOnBigStreets(AbstractMovementPattern):
    def get_next_map_node(self, crt_map_node, last_map_node):
        roads = singletons.spatial_singleton.roads
        quality = 5
        list_of_possible_roads = roads.get_list_of_next_roads_with_quality_restriction_for_cars(crt_map_node, quality)
        length = len(list_of_possible_roads)
        while (length < 1 and quality > 0):
            quality -= 1
            list_of_possible_roads = roads.get_list_of_next_roads_with_quality_restriction_for_cars(crt_map_node,
                                                                                                    quality)
            less_quality_list_of_roads = roads.get_list_of_next_roads_with_quality_restriction_for_cars(crt_map_node,
                                                                                                        quality - 1)
            list_of_possible_roads.extend(less_quality_list_of_roads)
            length = len(list_of_possible_roads)
            if (quality == 1 and length == 0):
                return None

        index = 0
        if (length >= 2):
            if last_map_node is not None:
                list_of_possible_roads = [road for road in list_of_possible_roads if (
                    road.get_start_point().getId() != last_map_node.getId() and road.get_end_point().getId() != last_map_node.getId())]
            index = randint(0, len(list_of_possible_roads) - 1)

        possible_road = list_of_possible_roads[index]
        if (possible_road.get_start_point().getId() == crt_map_node.getId()):
            return possible_road.get_end_point()
        else:
            return possible_road.get_start_point()

    def get_speed(self):
        return randint(5, 15)
