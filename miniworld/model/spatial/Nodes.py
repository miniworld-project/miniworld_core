
# encoding: utf-8
from miniworld.model.collections.DistanceMatrix import DistanceMatrix

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from UserList import UserList
from collections import OrderedDict

import geojson
from miniworld.model.spatial.Node.DefaultNode import DefaultNode
from miniworld.model.spatial.Node.MoveOnBigStreetsNode import MoveOnBigStreetsNode
from miniworld.model.spatial.Node.ArmaNode import ArmaNode
from miniworld.model.spatial.Node.ReplayNode import ReplayNode
from miniworld.model.singletons.Singletons import singletons
from miniworld.Scenario import scenario_config

class Nodes(object):
    ''' abstraction of current state of all nodes
    Parameter
    ---------
    list_of_movements_with_number_of_nodes :    list<(String, int)>
    
    Attributes
    ----------
    singleton                                   Singleton
    roads                                       Roads
    dict_of_nodes :                             dict<int, AbstractNode>
    '''
    def __init__(self, dict_of_node_types_with_number_of_nodes):
        self.roads = singletons.spatial_singleton.get_roads()
        self.dict_of_nodes = {}
        crnt_node_number = 0
        for (node_type, number) in dict_of_node_types_with_number_of_nodes.items():
            # TODO: use 1 as start idx not 0
            for i in range(number):
                self.crnt_node_id_in_type = i
                self.dict_of_nodes[crnt_node_number] = self.__get_node_for_name(node_type)
                crnt_node_number += 1
    
    def get_list_of_nodes(self):
        ''' 
        Returns
        -------
        dict<int, AbstractNode>
            of existing nodes
        '''
        return self.dict_of_nodes

    def get_node_for_node_id(self, node_id):
        '''
        Returns
        -------
        AbstractNode
        '''
        return self.dict_of_nodes[node_id]

    def get_distance_matrix(self):
        distance_matrix = DistanceMatrix.factory()()

        # TODO: REPLACE all calls with this
        # singletons.simulation_manager.get_emulation_node_ids(): -> range(scenario_config.get_number_of_nodes())
        for n in range(scenario_config.get_number_of_nodes()-1):
            for i in range(n + 1, scenario_config.get_number_of_nodes()):
                if n != i:

                    distance_matrix.set_distance(n+1, i+1, self.dict_of_nodes[n].get_distance_in_m(self.dict_of_nodes[i]))
        return distance_matrix

    def get_coordinates(self):
        '''
        Returns
        -------
        dict<int, (float, float)>
        '''
        return {n: self.__get_coordinates_for_single_node(n) for n in range(scenario_config.get_number_of_nodes()) }

    def get_geo_json(self):
        '''
        Returns
        -------
        geo_json
                    for the current state of all nodes
        '''
        feature_coll_nodes = geojson.FeatureCollection([self.__get_geo_json_for_single_node(n) for n in range(scenario_config.get_number_of_nodes())])
        return  geojson.dumps(feature_coll_nodes)

    def __get_coordinates_for_single_node(self, n):
        node = self.dict_of_nodes[n]
        return (float(node.get_lon()) , float(node.get_lat()))

    def __get_geo_json_for_single_node(self, n):
        node = self.dict_of_nodes[n]
        #type = node.get_name_of_movement_patter()

        return OrderedDict(
            type = "Feature",
            geometry = OrderedDict(
                type = "Point",
                coordinates = [float(node.get_lon()) , float(node.get_lat())]
            ),
            properties = OrderedDict(
                name = "Node " + str(n),
                #type = str(type),
                popupContent = "Node " + str(n)
            ),
        )


    def __get_node_for_name(self, name):
        if(name == "RandomWalk"):
            return DefaultNode(self.crnt_node_id_in_type)
        elif(name == "MoveOnBigStreets"):
            return MoveOnBigStreetsNode(self.crnt_node_id_in_type)
        elif(name == "Arma"):
            return ArmaNode(self.crnt_node_id_in_type)
        elif(name == "Replay"):
            return ReplayNode(self.crnt_node_id_in_type)
        else:
            return DefaultNode(self.crnt_node_id_in_type)