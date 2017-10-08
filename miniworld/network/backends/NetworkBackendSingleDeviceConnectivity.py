from miniworld.network.backends import NetworkBackend
from miniworld.service.network import NetworkConfiguratorP2P
from miniworld.singletons import singletons


class NetworkBackendSingleDeviceConnectivity(NetworkBackend.NetworkBackend()):

    def __init__(self, *args, **kwargs):
        super(NetworkBackendSingleDeviceConnectivity, self).__init__(*args, **kwargs)
        self.reset()

    def reset(self):
        self.net_configurator = NetworkConfiguratorP2P(singletons.network_backend.get_interface_index)

    def after_distance_matrix_changed(self, simulation_manager, network_backend, distance_matrix, **kwargs):

        # NOTE: we need to reuse the existing configurators due to their internal state!
        if singletons.scenario_config.is_network_links_auto_ipv4():

            new_connections = self.get_new_connections_with_interfaces_since_last_distance_matrix_change()
            step_cnt = simulation_manager.current_step

            # only connection setup and check for new connections
            self.net_configurator_p2p(new_connections)

            # perform full topology check
            if singletons.scenario_config.is_connectivity_check_enabled():
                # in the first step `new_connections` are all connections -> no need to check the full topology again!
                if step_cnt > 1:
                    self.net_configurator_p2p.apply_nic_configuration_commands({},
                                                                               self.net_configurator_p2p.get_nic_check_commands())
