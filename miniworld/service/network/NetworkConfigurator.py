import ipaddress
from io import StringIO

import miniworld.config.Scenario
from miniworld import singletons
from miniworld.errors import Base
from miniworld.network.connection import AbstractConnection
from miniworld.service.emulation.interface import InterfaceService
from miniworld.service.persistence.connections import ConnectionPersistenceService
from miniworld.service.persistence.interfaces import InterfacePersistenceService
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.util import NetUtil, ConcurrencyUtil


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
        self._interface_service = InterfaceService()
        self._interface_persistence_service = InterfacePersistenceService()

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

        self._node_persistence_service = NodePersistenceService()
        self._connection_persistence_service = ConnectionPersistenceService()

    def reset(self):
        self.nic_check_commands = {}

    def needs_reconfiguration(self, step_cnt):
        return step_cnt < 1

    def get_nic_check_commands(self):
        return self.nic_check_commands

    # TODO: move to EmulationService ?
    def run_emulation_node_commands(self, commands_per_emulation_node, ev, cnt_minions=None):
        results = []
        # run over EmulationNode s and set up the network
        with ConcurrencyUtil.network_provision_parallel() as executor:

            for emu_node, commands in sorted(commands_per_emulation_node.items(), key=lambda x: x[0]._id):
                commands = '\n'.join(commands)

                def _exec(virtualization_layer, commands):
                    if commands:
                        virtualization_layer.run_commands_eager_check_ret_val(StringIO(commands))

                    # notify EventSystem
                    # TODO:
                    # ev.update([virtualization_layer.node._id], 1.0, add=True)

                future = executor.submit(_exec, singletons.network_backend_bootstrapper.emulation_service.virtualization_layers[emu_node._id], commands)
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

    def configure_connection(self, connection: AbstractConnection):
        """
        Configure a single connection.

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
