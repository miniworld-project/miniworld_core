from miniworld.singletons import singletons

# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class SimulationStep:
    """
    Parameter
    ---------

    """

    def __init__(self):
        self.dict_of_coordinates = {}
        self.distances = {}

    def set_coordinate_for_node(self, node_id, coordinate):
        self.dict_of_coordinates[node_id] = coordinate

    def set_dict_of_coordinates(self, dict_of_coordinates):
        for node_id, coordinate in dict_of_coordinates:
            self.set_coordinate_for_node(node_id, coordinate)

    def set_distance_for_tuple_of_nodes(self, node_id_1, node_id_2, distance):
        self.distances[(node_id_1, node_id_2)] = distance

    def set_dict_of_distances(self, dict_of_distances):
        for node_id_1, node_id_2, distance in dict_of_distances:
            self.set_distance_for_tuple_of_nodes(node_id_1, node_id_2, distance)

    def to_string(self):
        result = "#######################################\n"
        for node_id, coodinates in self.dict_of_coordinates:
            result += node_id + "; (" + coodinates[0] + "," + coodinates[1] + ")\n"

        result += "-----------------------------------------\n"
        for i in range(0, singletons.scenario_config.get_number_of_nodes()):
            for j in range(0, singletons.scenario_config.get_number_of_nodes()):
                result += self.distances[(i, j)]
            result += "\n"
