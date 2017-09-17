
from collections import defaultdict
from pprint import pformat
from threading import Lock

from miniworld.Scenario import scenario_config
from miniworld.log import log
from miniworld.model.network.backends.NetworkBackend import NetworkBackendDummy

from miniworld.util import CoreConfigFileParser
from miniworld.util import DictUtil

# static lock for static methods ...
static_lock = Lock()


def NetworkBackendStatic():
    class NetworkBackendStatic(NetworkBackendDummy):
        '''
        Base class for static :py:class:`.NetworkBackend`s.

        They are static because the connections are known beforehand.
        There is no :py:class:`.MovevementDirector` which moves the nodes according to a model.
        '''

        def __init__(self, *args, **kwargs):
            super(NetworkBackendStatic, self).__init__(*args, **kwargs)
            self._all_connections = None

        def get_all_connections(self):
            '''
            Get all the connections the nodes will have to each other.

            Returns
            -------
            dict<int, set<int>>
                The connections each node has. Sorted by id asc. id number.
                Fully staffed matrix.
            '''

            # we need a lock here, otherwise all threads (each node) try to read the config file simultaneously!
            # used by each :py:class:`.EmulationNode`
            with static_lock:
                if self._all_connections is not None:
                    return self._all_connections

                core_scenarios = scenario_config.get_core_scenarios()
                all_connections = defaultdict(set)
                for _, core_scenario_path in core_scenarios:
                    connections_dict = CoreConfigFileParser.parse_core_config_file(core_scenario_path)
                    for k, v in connections_dict.items():
                        all_connections[k].update(v)

                all_connections = DictUtil.to_fully_staffed_matrix(all_connections)

                self._all_connections = all_connections

                log.info("connections: %s", pformat(all_connections))

                return all_connections

    return NetworkBackendStatic
