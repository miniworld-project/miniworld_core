from miniworld.management.spatial.MovementDirectorAbstract import MovementDirectorAbstract
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.spatial import CoreConfigNodes


class MovementDirectorCoreConfig(MovementDirectorAbstract):
    """
    Attributes
    ----------
    scenario_changes : list<list<str, int>>
        Describes the change of a scenario. The values are the steps until the next scenario becomes active.

    node_count :                                int
    nodes :                                     ArmaNodes
    """

    def __init__(self, scenario_changes, *args, **kwargs):
        self.nodes = CoreConfigNodes.factory()(scenario_changes)

    def get_distances_from_nodes(self):
        return self.nodes.get_distance_matrix()

    def get_geo_json_for_connections(self):
        return ""

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
        return self.nodes.walk()
