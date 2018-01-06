from collections import defaultdict, OrderedDict, Counter

from miniworld.network.connection import AbstractConnection
from miniworld.nodes.EmulationService import EmulationService
from miniworld.nodes.EmulationNodes import EmulationNodes
from miniworld.service.network.NetworkConfigurator import NetworkConfigurator, \
    NoMoreSubnetsAvailable, SubnetNoMoreIps
from miniworld.service.network.NetworkConfiguratorConnectionLess import NetworkConfiguratorConnectionLess
from miniworld.singletons import singletons


class NetworkConfiguratorSameSubnet(NetworkConfiguratorConnectionLess):
    """
    This configurator uses the node list to configure each interface.
    NOTE: the configurator has to run only once to configure all interfaces (in contrast to a connection-based configurator),
        but each step the new active connections can be checked for connectivity.
    Each interface is put into a different subnet. Even interfaces of the same type but with a different `nr_host_interface` attribute.

    Attributes
    ----------
    base_network_cidr : str, optional (default is the value from the scenario config)
        The network from which the subnets are generated.
    ips : OrderedDict<tuple<EmulationNode, Interface>, str>
        For each link store the allocated ip.
    """

    ################################################
    # NetworkConfigurator
    ################################################

    def __init__(self, *args, **kwargs):

        super(NetworkConfiguratorSameSubnet, self).__init__(*args, **kwargs)

        self._logger = singletons.logger_factory.get_logger(self)
        self.subnets = {}
        self.ips = OrderedDict()

    def get_subnet(self, interface):
        """

        Parameters
        ----------
        interface

        Returns
        -------

        Raises
        ------
        NoMoreSubnetsAvailable
        """
        # use for each `class_id` and `nr_host_interface` a different subnet
        key = interface.class_id, interface.nr_host_interface
        if key not in self.subnets:
            try:
                self.subnets[key] = next(self.subnet_generator)
            except StopIteration:
                raise NoMoreSubnetsAvailable("All /%s subnets from base network: %s used!" % (self.prefixlen, self.base_network_cidr))
        return self.subnets[key]

    def configure_connection(self, emulation_node: EmulationService):
        assert emulation_node._id is not None
        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        c = Counter()

        normal_ifaces = self._interface_service.filter_normal_interfaces(emulation_node.interfaces)

        for idx, interface in enumerate(normal_ifaces):
            assert interface._id is not None
            assert interface.class_id is not None
            assert interface.name is not None

            idx_iface = self.get_interface_index_fun(emulation_node, interface)
            c = Counter(list(c.keys()) + [interface.class_id])
            subnet = self.get_subnet(interface)

            key = self.get_key_ip_dict(emulation_node, interface)
            ip_addr = self.ips.get(key, None)

            if not ip_addr:
                # first offset is 0
                # this solution is usable in the distributed scenario without global state
                # TODO: this works only for situations where all nodes have the same number of interfaces!
                cnt_type_ifaces = c[interface.class_id]
                assert cnt_type_ifaces >= 1
                offset = (emulation_node._id + 1)
                ip_addr = self.get_ip(subnet, offset=offset - 1)
            netmask = subnet.netmask

            ip_set_command_up = NetworkConfigurator.get_ip_addr_change_cmd(self.get_nic_name(idx_iface), ip_addr, netmask)
            self._interface_persistence_service.update_ipv4(interface=interface, ipv4=str(ip_addr))
            commands_per_node[emulation_node].append(ip_set_command_up)

            # remember allocated ip
            self.ips[key] = ip_addr

        # the check commands cannot be calculated now, first all ips have to be allocated
        # we delay the creation of the check commands until :py:meth:`.get_nic_check_commands` is called
        return commands_per_node, {}

    def get_ip(self, subnet, offset=0):
        try:
            # skip net address (+1)
            return subnet[1 + offset]
        except IndexError:
            raise SubnetNoMoreIps("No more ips in subnet: '%s' available for offset: '%s'!" % (subnet, offset + 1))

    def get_nic_check_commands(self):
        """
        Do link checking connection-based, there check which nodes are reachable!

        In the distributed mode, we perform link checking on both sides!

        Parameters
        ----------
        connections

        Returns
        -------

        """
        self._logger.info("assuming bidirectional links ...")
        check_commands_per_node = defaultdict(list)

        for connection in self._connection_persistence_service.get_new(connection_type=AbstractConnection.ConnectionType.user):  # type: AbstractConnection

            # NOTE: for the distributed mode, we have to check which node is local and which is remote
            # because connections might not be fully staffed, we need to perform the check from the local node to the remote node!
            emulation_node_x, emulation_node_y = EmulationNodes([connection.emulation_node_x, connection.emulation_node_y]).sort_by_locality()

            interface_y = connection.interface_y

            def add_check_cmd(ip_addr):

                ping_cmd = self.connectivity_checker_fun(ip_addr, self.network_timeout)
                check_commands_per_node[emulation_node_x].append(ping_cmd)

            # for CentralNode let each node ping all allocated ips
            if EmulationNodes([emulation_node_y]).filter_central_nodes():
                for ip_addr in self.ips.values():
                    add_check_cmd(ip_addr)
            # check which ip is allocated to emulation_node_y
            else:
                # ip_addr = self.ips[self.get_key_ip_dict(emulation_node_y, interface_y)]
                ip_addr = interface_y.ipv4
                add_check_cmd(ip_addr)

        return check_commands_per_node

    def _reset_internal_state(self):
        self.counter = 0

    ################################################
    # Own impl
    ################################################

    def get_key_ip_dict(self, emulation_node, interface):
        return emulation_node._id, interface._id
