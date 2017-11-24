from collections import defaultdict

from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.network.NetworkConfigurator import NetworkConfigurator
from miniworld.util import DictUtil


class NetworkConfiguratorConnectionBased(NetworkConfigurator):
    """
    Based on the current connections (including the interfaces), the network cards can be configured (e.g. IP).
    """

    def get_nic_configuration_commands(self):
        """
        Get the configuration commands needed to configure the network and precalculate the check commands if possible yet.

        Returns
        -------
        dict<EmulationNode, list<str>>
            First entry are the commands for network configuration.
        """

        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        check_commands_per_node = defaultdict(list)

        for connection in self._connection_persistence_service.get_new(connection_type=AbstractConnection.ConnectionType.user):  # type: AbstractConnection

            # get nic configuration commands + check commands per connection
            _commands_per_node, _check_commands_per_node = self.configure_connection(connection)
            # update dicts
            commands_per_node = DictUtil.list_merge_values(commands_per_node, _commands_per_node)
            check_commands_per_node = DictUtil.list_merge_values(check_commands_per_node, _check_commands_per_node)

        # The commands for network checking may not be available at this time. But if they are,
        # they are stored for later retrieval so that they need to be calculated only once.
        self.nic_check_commands = DictUtil.list_merge_values(self.nic_check_commands,
                                                             check_commands_per_node)

        return commands_per_node

    def filter_emulation_nodes(self, emulation_nodes):
        """
        Use a node filter for the ip provisioning.

        Parameters
        ----------
        emulation_nodes : EmulationNodes

        Returns
        -------
        bool
        """
        # only emulation_node_x has to be a real EmulationNode
        return len(emulation_nodes.filter_real_emulation_nodes()) > 0

        # return True

    def filter_interfaces(self, interfaces):
        """
        Use a interface filter for the ip provisioning.

        Parameters
        ----------
        interfaces : Interfaces

        Returns
        -------
        bool
        """
        return len(interfaces.filter_normal_interfaces()) > 0
        # return True
