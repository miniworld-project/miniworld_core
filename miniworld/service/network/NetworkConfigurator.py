import ipaddress
from io import StringIO

import miniworld.config.Scenario
from miniworld import singletons
from miniworld.errors import Base
from miniworld.util import DictUtil, NetUtil, ConcurrencyUtil


class NetworkConfiguratorError(Base):
    pass


class NetworkConfigurator:

    """
    Base class for network configuraters.

    Moreover, the network can be checked for connectivity and whether the NIC configuration succeeded.
    For this purpose a `connectivity_checker_fun` function can be supplied which uses e.g. ICMP for checking.

    Attributes
    ----------
    nic_prefix : str, optional (default is taken from the scenario config)
        E.g. 'eth'
    nic_check_commands : nic_check_commands
    """

    def __init__(self, get_interface_index_fun, nic_prefix=None,
                 # connectivity checking stuff
                 connectivity_checker_fun=None, is_connectivity_checks_enabled=None, network_timeout=None,
                 base_network_cidr=None, prefixlen=None,
                 **kwargs):
        """

        Parameters
        ----------
        get_interface_index_fun : EmulationNode -> Interface -> int
            Get the interface index.
        connectivity_checker_fun : str, float -> str, optional (default is :py:meth:`.get_scenario_config_checker`)
            Generates the command which shall be executed on the node to check
             the connectivity.

        nic_prefix : str, optional (default is taken from the scenario config)
        is_connectivity_checks_enabled : bool, optional (default is True)

        network_timeout : float, optional (default is taken from the scenario config)

        base_network_cidr : str, optional (default is the value from the scenario config)
            The network from which the subnets are generated.

        prefixlen : str, optional (default is the value from the scenario config)
            Assigns for each node a /x network. 30 is the smallest subnet size for broadcast included.

        """
        if nic_prefix is None:
            nic_prefix = miniworld.config.Scenario.scenario_config.get_network_links_nic_prefix()
        if network_timeout is None:
            network_timeout = miniworld.config.Scenario.scenario_config.get_connectivity_check_timeout()
        if is_connectivity_checks_enabled is None:
            is_connectivity_checks_enabled = miniworld.config.Scenario.scenario_config.is_connectivity_check_enabled()
        if connectivity_checker_fun is None:
            connectivity_checker_fun = self.get_scenario_config_checker

        self._logger = singletons.logger_factory.get_logger(self)

        self.get_interface_index_fun = get_interface_index_fun
        self.connectivity_checker_fun = connectivity_checker_fun
        self.is_connectivity_checks_enabled = is_connectivity_checks_enabled
        self.network_timeout = network_timeout
        self.nic_prefix = nic_prefix

        self.nic_check_commands = {}

        if base_network_cidr is None:
            base_network_cidr = singletons.scenario_config.get_network_configuration_ip_provisioner_base_network_cidr()
        if prefixlen is None:
            prefixlen = singletons.scenario_config.get_network_configuration_ip_provisioner_prefixlen()

        self.base_network_cidr = base_network_cidr
        self.prefixlen = prefixlen

        # needed for `ipaddress` module
        base_network_cidr = base_network_cidr

        # /x subnet generator
        self.subnet_generator = NetUtil.get_slash_x(ipaddress.ip_network(base_network_cidr).subnets(), prefixlen)

    def reset(self):
        self.nic_check_commands = {}

    def needs_reconfiguration(self, step_cnt):
        return step_cnt < 1

    def get_nic_check_commands(self, connections):
        """
        Parameters
        ----------
        connections : dict<(EmulationNode,EmulationNode), iterable<(Interface, Interface)]>>
            Must be fully staffed if you want bidirectional links!
        """
        return self.nic_check_commands

    def get_active_connections(self):
        # get all active connections
        active_interfaces_per_connection = singletons.network_manager.connection_store.get_active_interfaces_per_connection()
        # fully staffed matrix
        active_interfaces_per_connection = DictUtil.to_fully_staffed_matrix_2(active_interfaces_per_connection)

        return active_interfaces_per_connection

    def run_emulation_node_commands(self, commands_per_emulation_node, ev, cnt_minions=None):
        results = []
        # run over EmulationNode s and set up the network
        with ConcurrencyUtil.network_provision_parallel() as executor:

            for emu_node, commands in sorted(commands_per_emulation_node.items()):
                commands = '\n'.join(commands)

                def _exec(emu_node, commands):
                    if commands:
                        self._logger.debug("network config for node: %s:\n%s", emu_node._id, commands)
                        emu_node.virtualization_layer.run_commands_eager_check_ret_val(StringIO(commands))

                    # notify EventSystem
                    ev.update([emu_node._id], 1.0, add=True)

                future = executor.submit(_exec, emu_node, commands)
                results.append(future)

            # wait for results
            for f in results:
                f.result()

    def apply_nic_configuration_commands(self, commands_per_node):
        es = singletons.event_system

        # first setup the whole network
        # clear all progress, a scenario change requires to clear the progress
        with es.event_init(es.EVENT_NETWORK_SETUP) as ev:
            self.run_emulation_node_commands(commands_per_node, ev)

    def apply_nic_check_commands(self, check_commands_per_node):
        es = singletons.event_system

        # check the connectivity
        if self.is_connectivity_checks_enabled:
            with es.event_init(es.EVENT_NETWORK_CHECK) as ev:

                self._logger.info("Doing connectivity checks ...")
                # NOTE: do not stress the network
                self.run_emulation_node_commands(check_commands_per_node, ev)
        else:
            with es.event_init(es.EVENT_NETWORK_CHECK) as ev:
                ev.finish()

    def configure_connection(self, emulation_nodes, interfaces):
        """
        Configure a single connection.

        Parameters
        ----------
        emulation_nodes : EmulationNodes
        interfaces : Interfaces

        Returns
        -------
        dict<EmulationNode, list<str>>, dict<EmulationNode, list<str>>
        """
        raise NotImplementedError

    @staticmethod
    # TODO: MOVE TO NETWORK UTIL!
    def get_ip_addr_change_cmd(dev, ip, netmask, up=True):
        return 'ifconfig {dev} {ip} netmask {netmask} {state}'.format(dev=dev, ip=ip, netmask=netmask,
                                                                      state='up' if up else '')

    def get_nic_name(self, idx):
        return '%s%s' % (self.nic_prefix, idx)

    def get_ip(self, subnet, offset=0):
        raise NotImplementedError

    #########################################
    # Connectivity Checkers
    #########################################

    # TODO: add interface? => check that the ip is reachable from the correct interface
    def get_scenario_config_checker(self, ip, timeout):
        """
        ICMP network connectivity checker.

        Parameters
        ----------
        ip : str
        timeout : float

        Returns
        -------
        """
        cmd = singletons.scenario_config.get_connectivity_check_cmd()
        return cmd.format(ip=ip, timeout=timeout)


class NoMoreSubnetsAvailable(NetworkConfiguratorError):
    pass


class SubnetNoMoreIps(NetworkConfiguratorError):
    pass
