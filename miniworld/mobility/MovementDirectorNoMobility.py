from miniworld.mobility import DistanceMatrix
from miniworld.mobility.MovementDirectorAbstract import MovementDirectorAbstract


class MovementDirectorNoMobility(MovementDirectorAbstract):

    def get_distances_from_nodes(self):
        return DistanceMatrix.factory()()

    def get_geo_json_for_nodes(self):
        """
        Returns
        -------
        geo_json
                    for the current state of all nodes
        """
        return ""

    def get_geo_json_for_roads(self):
        """
        Returns
        -------
        geo_json
                    for the current state of all nodes
        """
        return ""

    def simulate_one_step(self):
        return 1
