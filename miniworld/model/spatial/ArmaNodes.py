
# encoding: utf-8
from miniworld.model.singletons.Singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from time import strptime
from collections import OrderedDict

import geojson

from miniworld.model.spatial.Node.ArmaNode import ArmaNode


class ArmaNodes:
    def __init__(self, node_cnt):
        self.file = open(singletons.spatial_singleton.file_path, "r")
        self.node_cnt = node_cnt
        self.crnt_line = self.file.readline()
        self.start_time_data = self.__extract_time_from_line(self.crnt_line)
        self.list_of_nodes = [ArmaNode() for _ in range(node_cnt)]
        self.next_step = self.get_next_step_from_file()

    def get_distance_matrix(self):
        output = {}
        for n in range(0, self.node_cnt - 1):
            for i in range(n + 1, self.node_cnt):
                if n != i:
                    output[(n+1, i+1)] = self.list_of_nodes[n].get_distance_in_m(self.list_of_nodes[i])
        return output

    def walk(self):
        if self.next_step is None:
            self.get_next_step_from_file()
        index = 0
        for step in self.next_step[1]:
            self.list_of_nodes[index].walk(step)
            index += 1
        self.get_next_step_from_file()

    def get_next_step_from_file(self):
        while("POSITIONLIST_BEGIN" not in self.file.readline()):
            pass

        self.crnt_line = self.file.readline()
        next_time = self.__extract_time_from_line(self.crnt_line)
        list_of_coordinates = []
        while("POSITIONLIST_END" not in self.crnt_line):
            list_of_coordinates.append(self.__extract_coordinates_from_line(self.crnt_line))
            self.crnt_line = self.file.readline()
        self.next_step = (next_time, list_of_coordinates)


    def get_geo_json(self):
        '''
        Returns
        -------
        geo_json
                    for the current state of all nodes
        '''
        feature_coll_nodes = geojson.FeatureCollection([self.__get_single_node(n) for n in range(self.node_cnt)])
        return  geojson.dumps(feature_coll_nodes)

    def __extract_coordinates_from_line(self, line):
        first_index = line.find("\"[") + 2
        second_index =line.find("]\"")
        coordinates = line[first_index:second_index]
        list_of_cords = coordinates.split(",")
        return (float(list_of_cords[0]), float(list_of_cords[1]))

    def __extract_time_from_line(self, line):
        return strptime(line[0:7], "%H:%M:%S")

    def __get_single_node(self, n):
        node = self.list_of_nodes[n]

        return OrderedDict(
            type = "Feature",
            geometry = OrderedDict(
                type = "Point",
                coordinates = [float(node.get_lon()) , float(node.get_lat())]
            ),
            properties = OrderedDict(
                color = node.color,
                name = "Node " + str(n),
                type = "Arma" + str(n),
                popupContent = "Node " + str(n)
            ),
        )