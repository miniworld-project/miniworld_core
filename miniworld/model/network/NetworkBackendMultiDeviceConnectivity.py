from miniworld.Scenario import scenario_config
from miniworld.management.network.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.network.backends import NetworkBackend


class NetworkBackendMultiDeviceConnectivity(NetworkBackend.NetworkBackend()):

    def __init__(self, *args, **kwargs):
        super(NetworkBackendMultiDeviceConnectivity, self).__init__(*args, **kwargs)
        self.reset()

    def reset(self):
        self.net_configurator = NetworkConfiguratorSameSubnet(singletons.network_backend.get_interface_index)

    def after_distance_matrix_changed(self, simulation_manager, network_backend, distance_matrix, **kwargs):

        # TODO:
        # NOTE: we need to reuse the existing configurators due to their internal state!
        if scenario_config.is_network_links_auto_ipv4():
            new_connections = singletons.network_manager.get_new_connections_with_interfaces_since_last_distance_matrix_change()
            # only connection setup and check for new connections
            self.net_configurator_p2p(new_connections)

            # perform full topology check
            if scenario_config.is_connectivity_check_enabled():
                # in the first step `new_connections` are all connections -> no need to check the full topology again!
                if simulation_manager.step_cnt > 1:
                    self.net_configurator_p2p.apply_nic_configuration_commands({}, self.net_configurator_p2p.get_nic_check_commands())
