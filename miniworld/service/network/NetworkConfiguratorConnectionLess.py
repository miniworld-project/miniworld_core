from collections import defaultdict

from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.network.NetworkConfigurator import NetworkConfigurator
from miniworld.util import DictUtil


class NetworkConfiguratorConnectionLess(NetworkConfigurator):
    """
    This IP provisioner iterates over the list of nodes instead of the connections.
    """

    def allocate_ips(self):
        for emulation_node in self._node_persistence_service.all(connection_type=AbstractConnection.ConnectionType.user):
            # get nic configuration commands + check commands per connection
            self.configure_connection(emulation_node)

    def get_nic_configuration_commands(self):
        """
        Get the configuration commands needed to configure the network and the check commands.

        Returns
        -------
        dict<EmulationNode, list<str>>, dict<EmulationNode, list<str>>
            First entry are the commands for network configuration, second for the network checking.
        """

        self._reset_internal_state()

        # TODO: do only once!
        self._logger.info("preallocate IPs ...")
        self.allocate_ips()

        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        check_commands_per_node = defaultdict(list)

        for emulation_node in self._node_persistence_service.all(connection_type=AbstractConnection.ConnectionType.user):
            # get nic configuration commands + check commands per connection
            _commands_per_node, _check_commands_per_node = self.configure_connection(emulation_node)
            # update dicts
            commands_per_node = DictUtil.list_merge_values(commands_per_node, _commands_per_node)
            check_commands_per_node = DictUtil.list_merge_values(check_commands_per_node, _check_commands_per_node)

        self.nic_check_commands = DictUtil.list_merge_values(self.nic_check_commands,
                                                             check_commands_per_node)

        return commands_per_node
