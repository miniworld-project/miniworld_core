from collections import defaultdict, OrderedDict, Counter

from miniworld.log import log
from miniworld.management.network.manager.provisioner.NetworkConfigurator import NetworkConfigurator, \
    NoMoreSubnetsAvailable, SubnetNoMoreIps
from miniworld.management.network.manager.provisioner.NetworkConfiguratorConnectionLess import \
    NetworkConfiguratorConnectionLess
from miniworld.model.emulation.nodes.EmulationNodes import EmulationNodes


class NetworkConfiguratorSameSubnet(NetworkConfiguratorConnectionLess):

    '''
    This configurator uses the node list to configure each interface.
    NOTE: the configurator has to run only once to configure all interfaces (in contrast to a connection-based configurator),
        but each step the new active connections can be checked for connectivity.
    Each interface is put into a different subnet. Even interfaes of the same type but with a different `nr_host_interface` attribute.

    Attributes
    ----------
    base_network_cidr : str, optional (default is the value from the scenario config)
        The network from which the subnets are generated.
    subnet_counter : defaultdict<subnet, int>
        For each subnet store the number of allocated ips.
    ips : OrderedDict<tuple<EmulationNode, Interface>, str>
        For each link store the allocated ip.
    '''

    ################################################
    ### NetworkConfigurator
    ################################################

    def __init__(self, *args, **kwargs):

        super(NetworkConfiguratorSameSubnet, self).__init__(*args, **kwargs)

        self.subnets = {}
        self.subnet_counter = defaultdict(lambda: 0)
        self.ips = OrderedDict()

    def get_subnet(self, interface):
        '''

        Parameters
        ----------
        interface

        Returns
        -------

        Raises
        ------
        NoMoreSubnetsAvailable
        '''
        if not interface in self.subnets:
            try:
                self.subnets[interface] = next(self.subnet_generator)
            except StopIteration:
                raise NoMoreSubnetsAvailable("All /%s subnets from base network: %s used!" % (self.prefixlen, self.base_network_cidr))
        return self.subnets[interface]

    def configure_connection(self, emulation_node, connections):
        '''

        Parameters
        ----------
        emulation_node : EmulationNode
        connections : OrderedDict<EmulationNodes, tuple<Interfaces>>
            Must be fully staffed if you want bidirectional links!
        '''
        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        c = Counter()
        normal_ifaces = emulation_node.network_mixin.interfaces.filter_normal_interfaces()
        for idx, interface in enumerate(normal_ifaces):
            idx_iface = self.get_interface_index_fun(emulation_node, interface)
            c = Counter(c.keys() + [interface])
            subnet = self.get_subnet(interface)

            key = self.get_key_ip_dict(emulation_node, interface)
            ip_addr = self.ips.get(key, None)

            if not ip_addr:
                # first offset is 0
                # this solution is usable in the distributed scenario without global state
                # TODO: this works only for situations where all nods have the same number of interfaces!
                cnt_total_type_ifaces = len(emulation_node.network_mixin.interfaces.filter_type(type(interface)))
                # NOTE: we do not use the type here! instead the count the interfaces (different eq operation)!
                cnt_type_ifaces = c[interface]

                offset = emulation_node.id * (cnt_total_type_ifaces-cnt_type_ifaces+1)
                ip_addr = self.get_ip(subnet, offset=offset-1)
            netmask = subnet.netmask

            ip_set_command_up = NetworkConfigurator.get_ip_addr_change_cmd(self.get_nic_name(idx_iface), ip_addr, netmask)
            commands_per_node[emulation_node].append(ip_set_command_up)

            self.subnet_counter[subnet] += 1

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

    def get_nic_check_commands(self, connections):
        '''
        Do link checking connection-based, there check which nodes are reachable!

        In the distributed mode, we perform link checking on both sides!

        Parameters
        ----------
        connections

        Returns
        -------

        '''
        log.info("assuming bidirectional links ...")
        check_commands_per_node = defaultdict(list)

        for emulation_nodes, list_ifaces in connections.items():

            if not emulation_nodes.filter_real_emulation_nodes():
                break

            # NOTE: for the distributed mode, we have to check which node is local and which is remote
            # because connections might not be fully staffed, we need to perform the check from the local node to the remote node!
            emulation_node_x, emulation_node_y = emulation_nodes.sort_by_locality()

            for interfaces in list_ifaces:

                if not interfaces.filter_normal_interfaces():
                    break

                interface_x, interface_y = interfaces

                def add_check_cmd(ip_addr):

                    ping_cmd = self.connectivity_checker_fun(ip_addr, self.network_timeout)
                    check_commands_per_node[emulation_node_x].append(ping_cmd)

                # for CentralNode let each node ping all allocated ips
                if EmulationNodes([emulation_node_y]).filter_central_nodes():
                    for ip_addr in self.ips.values():
                        add_check_cmd(ip_addr)
                # check which ip is allocated to emulation_node_y
                else:
                    ip_addr = self.ips[self.get_key_ip_dict(emulation_node_y, interface_y)]
                    add_check_cmd(ip_addr)

        return check_commands_per_node

    def _reset_internal_state(self):
        self.counter = 0

    ################################################
    ### Own impl
    ################################################

    def get_key_ip_dict(self, emulation_node, interface):
        return emulation_node.id, interface