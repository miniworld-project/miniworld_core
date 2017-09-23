# encoding: utf-8
from miniworld.management.spatial.MovementDirectorAbstract import MovementDirectorAbstract
from miniworld.model.singletons.Singletons import singletons

from miniworld.model.spatial.ArmaNodes import ArmaNodes

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class MovementDirectorArma(MovementDirectorAbstract):
    """
    Attributes
    ----------
    node_count :                                int
    nodes :                                     ArmaNodes
    """

    def __init__(self, node_count, file_path):
        self.node_count = node_count
        self.nodes = ArmaNodes(self.node_count, file_path)

    def get_distances_from_nodes(self):
        return self.nodes.get_distance_matrix()

    def get_geo_json_for_nodes(self):
        """
        Returns
        -------
        geo_json
                    for the current state of all nodes
        """
        return self.nodes.get_geo_json()

    def get_geo_json_for_roads(self):
        """
        Returns
        -------
        geo_json
                    for the current state of all nodes
        """
        return ""

    def simulate_one_step(self):
        self.nodes.walk()

    def set_path_to_replay_file(self, path):
        singletons.spatial_singleton.set_file_path(path)
