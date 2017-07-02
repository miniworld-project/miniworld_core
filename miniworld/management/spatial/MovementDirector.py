
# encoding: utf-8
from miniworld.management.spatial.MovementDirectorAbstract import MovementDirectorAbstract

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from miniworld.model.spatial.Nodes import Nodes
from miniworld.Scenario import scenario_config
import geojson
from collections import OrderedDict
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.spatial.Roads import Roads




class MovementDirector(MovementDirectorAbstract):
    '''
    Attributes
    ----------
    dict_of_movements_with_number_of_nodes :    dict<str, int>
        Name of the movement pattern, count of nodes
    roads :                                     Roads
    nodes :                                     Nodes
    '''
    def __init__(self, dict_of_movements_with_number_of_nodes):
        self.roads = singletons.spatial_singleton.get_roads()
        self.nodes = Nodes(dict_of_movements_with_number_of_nodes)

    def get_distances_from_nodes(self):
        '''
        Returns
        -------
        dict<(int, int), float>
            The distance (meters) matrix for each connection.
        '''
        return self.nodes.get_distance_matrix()

    def get_geo_json_for_roads(self):
        ''' 
        Returns
        -------
        geo_json
            for the existing streets
        '''
        return self.roads.get_geo_json()

    def get_geo_json_for_nodes(self):
        '''
        Returns
        -------
        geo_json
            for the current state of all nodes
        '''
        return self.nodes.get_geo_json()

    def get_coordinates_for_nodes(self):
        '''
        Returns
        -------
        dict<int, (float, float)>
            with current coordinates of all nodes and id as key
        '''
        return self.nodes.get_coordinates()

    def get_geo_json_for_connections(self):
        '''
        Returns
        -------
        geojson
            with connection status for all nodes
        '''
        list_of_geo_json_objects = []

        for emulation_node, connected_emulation_nodes in singletons.network_manager.connection_store.get_connections_per_node().items():
            for connected_emulation_node in connected_emulation_nodes:
                list_of_geo_json_objects.append(self.__get_geo_json_object_for_connection(emulation_node.id-1, connected_emulation_node.id-1))

        feature_coll_roads = geojson.FeatureCollection(list_of_geo_json_objects)
        return geojson.dumps(feature_coll_roads)

    def __get_geo_json_object_for_connection(self, node_id_1, node_id_2):
        source = self.nodes.dict_of_nodes[node_id_1]
        target = self.nodes.dict_of_nodes[node_id_2]

        return OrderedDict(
            type = "Feature",
            geometry = OrderedDict(
                type = "LineString",
                coordinates = [[float(source.get_lon()) , float(source.get_lat())], [float(target.get_lon()) , float(target.get_lat())]]
            ),
            properties= OrderedDict(
                color = source.color,
                type = str(node_id_1),
                name = "Coors Field",
                amenity = "Baseball Stadium"
            )
        )

    def set_path_to_replay_file(self, path):
        singletons.spatial_singletonset_file_path(path)

    def simulate_one_step(self):
        '''
        simulates the next step for all nodes
        '''
        for node in self.nodes.get_list_of_nodes().items():
            node[1].step()

        #current_simulation_step = SimulationStep()
        #current_simulation_step.set_dict_of_coordinates(self.get_coordinates_for_nodes())
        #current_simulation_step.set_dict_of_distances(self.get_distances_from_nodes())
        #singletons.add_next_simulated_step(current_simulation_step)


