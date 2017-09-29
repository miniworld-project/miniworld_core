# encoding: utf-8
from pprint import pformat

from miniworld.Scenario import scenario_config
from miniworld.model.collections.DistanceMatrix import DistanceMatrix
from miniworld.model.singletons.Resetable import Resetable
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.spatial import logger
from miniworld.model.spatial.Location import Location

from miniworld.util.CoreConfigFileParser import parse_core_config_file, parse_core_config_file_positions

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


def factory():
    if scenario_config.is_core_mode_lan():
        return CoreConfigNodesLan
    elif scenario_config.is_core_mode_wifi():
        return CoreConfigNodesWiFi

    raise ValueError("Core mode '%s' not supported!" % scenario_config.get_core_mode())


class CoreConfigNodes(Resetable):
    """
    Parameter
    ---------
    scenario_changes : list<list<str, int>>
        Describes the change of a scenario. The values are the steps until the next scenario becomes active.
        The keys are the paths to the core xml path.

    Attributes
    ----------

    """

    def __init__(self, scenario_changes):
        self.orig_scenario_changes = scenario_changes
        self.reset()

    def reset(self):
        # use list as stack with first item first
        self.scenario_changes = list(reversed(self.orig_scenario_changes))

        self.remaining_seconds = None
        self.crnt_core_config_file = None

        logger().debug("scenario files: %s", self.scenario_changes)

    def get_list_of_nodes(self):
        """
        Stub-methode
        """
        return {}

    def get_node_for_node_id(self, node_id):
        """
        Stub-methode
        """
        return None

    # TODO: use distances from core config file
    def get_distance_matrix(self):
        # TODO: supply iterator function
        distance_matrix = DistanceMatrix.factory()()
        for n in range(0, range(scenario_config.get_number_of_nodes() - 1)):
            for i in range(n + 1, range(scenario_config.get_number_of_nodes())):
                if n != i:
                    if i in self.crnt_connections[n]:
                        # connected
                        distance = 0
                        distance_matrix.set_distance(n + 1, i + 1, distance)
                    else:
                        # not connected
                        distance_matrix.set_unlimited_distance(n + 1, i + 1)
        return distance_matrix

    def get_coordinates(self):
        """
        Stub-methode
        """
        return {}

    def get_geo_json(self):
        """
        Stub-methode
        """
        return ""

    def __get_next_scenario(self):
        """

        Returns
        -------
        str, int
        """
        if self.scenario_changes:
            return self.scenario_changes.pop()
        return []

    def walk(self):
        logger().info("step")

        if self.remaining_seconds is None or self.remaining_seconds <= 0:
            next_scenario = self.__get_next_scenario()
            if next_scenario:
                self.remaining_seconds, self.crnt_core_config_file = next_scenario
                # TODO: REMOVE WHEN FIXING keys_to_int()
                self.remaining_seconds = int(self.remaining_seconds)
                logger().debug("%s, %s" % (self.remaining_seconds, self.crnt_core_config_file))

                self._walk()

            else:
                if scenario_config.is_core_loop():
                    logger().info("end of core network files ... looping!")
                    self.reset()
                else:
                    logger().info("end of core network files ... keeping last scenario!")
        else:
            self.remaining_seconds -= singletons.simulation_manager.run_loop.time_step

        return 1

    def _walk(self):
        raise NotImplementedError


class CoreConfigNodesLan(CoreConfigNodes):
    def __init__(self, *args, **kwargs):
        super(CoreConfigNodesLan, self).__init__(*args, **kwargs)
        self.crnt_connections = None

    # TODO: use distances from core config file
    def get_distance_matrix(self):
        # TODO: supply iterator function
        distance_matrix = DistanceMatrix.factory()()
        for n in singletons.simulation_manager.get_emulation_node_ids():
            for i in range(n + 1, singletons.simulation_manager.get_emulation_node_ids()[-1] + 1):
                if n != i:
                    if i in self.crnt_connections[n]:
                        # connected
                        distance = 1
                        distance_matrix.set_distance(n, i, distance)
                    else:
                        # not connected
                        distance_matrix.set_unlimited_distance(n, i)
        return distance_matrix

    def _walk(self):
        # change the scenario
        self.crnt_connections = parse_core_config_file(self.crnt_core_config_file)
        logger().info("changing topology to '%s'", pformat(self.crnt_connections))


class CoreConfigNodesWiFi(CoreConfigNodes):
    def __init__(self, *args, **kwargs):
        super(CoreConfigNodesWiFi, self).__init__(*args, **kwargs)
        self.crnt_distances = None

    # TODO: use distances from core config file
    def get_distance_matrix(self):
        # TODO: supply iterator function
        distance_matrix = DistanceMatrix.factory()()
        for n in singletons.simulation_manager.get_emulation_node_ids():
            for i in range(n + 1, singletons.simulation_manager.get_emulation_node_ids()[-1] + 1):
                if n != i:
                    distance = Location(*self.crnt_distances[n]).get_distance_in_m(Location(*self.crnt_distances[i]))
                    distance_matrix.set_distance(n, i, distance)

        return distance_matrix

    def _walk(self):
        # change the scenario
        self.crnt_distances = parse_core_config_file_positions(self.crnt_core_config_file)
        if not self.crnt_distances:
            raise ValueError("Did you choose the wifi mode in Core? There are no node positions!")
        logger().info("changing positions to '%s'", pformat(self.crnt_distances))
