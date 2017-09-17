from collections import defaultdict

from miniworld import singletons
from miniworld.Scenario import scenario_config
from miniworld.management.network.manager.provisioner.NetworkConfigurator import NetworkConfigurator
from miniworld.model.emulation.nodes import EmulationNode
from miniworld.util import DictUtil
from miniworld.log import log


class NetworkConfiguratorConnectionLess(NetworkConfigurator):
    '''
    This IP provisioner iterates over the list of nodes instead of the connections.
    '''

    def allocate_ips(self):
        # TODO:
        for emulation_node in self.get_all_emulation_nodes():

            if not self.filter_emulation_node(emulation_node):
                continue

            # get nic configuration commands + check commands per connection
            self.configure_connection(emulation_node, None)

    def get_nic_configuration_commands(self, connections):
        '''
        Get the configuration commands needed to configure the network and the check commands.

        Parameters
        ----------
        connections : OrderedDict<EmulationNodes, tuple<Interfaces>>
            Must be fully staffed if you want bidirectional links!

        Returns
        -------
        dict<EmulationNode, list<str>>, dict<EmulationNode, list<str>>
            First entry are the commands for network configuration, second for the network checking.
        '''

        self._reset_internal_state()

        # TODO: do only once!
        log.info("preallocate IPs ...")
        self.allocate_ips()

        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        check_commands_per_node = defaultdict(list)

        # TODO:
        for emulation_node in self.get_emulation_nodes():

            if not self.filter_emulation_node(emulation_node):
                continue

            # get nic configuration commands + check commands per connection
            _commands_per_node, _check_commands_per_node = self.configure_connection(emulation_node, None)
            # update dicts
            commands_per_node = DictUtil.list_merge_values(commands_per_node, _commands_per_node)
            check_commands_per_node = DictUtil.list_merge_values(check_commands_per_node, _check_commands_per_node)

        self.nic_check_commands = DictUtil.list_merge_values(self.nic_check_commands,
                                                             check_commands_per_node)

        return commands_per_node

    def get_emulation_nodes(self):
        return singletons.simulation_manager.get_emulation_nodes()

    def get_all_emulation_nodes(self):
        for node_id in scenario_config.get_all_emulation_node_ids():
            yield EmulationNode.EmulationNode.factory(node_id)

    def filter_emulation_node(self, emulation_node):
        '''
        Use a node filter for the ip provisioning.

        Parameters
        ----------
        emulation_node : EmulationNode

        Returns
        -------
        bool
        '''
        return True

    def configure_connection(self, emulation_node):
        '''
        Configure a single connection.

        Parameters
        ----------
        emulation_node : EmulationNode

        Returns
        -------
        dict<EmulationNode, list<str>>, dict<EmulationNode, list<str>>
        '''
        raise NotImplementedError
