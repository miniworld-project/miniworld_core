from collections import defaultdict

from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.network.NetworkConfiguratorConnectionBased import \
    NetworkConfiguratorConnectionBased


class NetworkConfiguratorP2P(NetworkConfiguratorConnectionBased):
    """
    Provisions IP address based on the current connections.
    For each connection, a link with an own subnet is created.

    Attributes
    ----------
    subnet_generator : generator<IPv4Network>
    used_subnets : dict<(EmulationNode, EmulationNode), ipaddress.IPv4Network>
        The subnet for each connection.
    """

    ################################################
    # NetworkConfigurator
    ################################################

    def __init__(self, *args, **kwargs):

        super(NetworkConfiguratorP2P, self).__init__(*args, **kwargs)

        self.used_subnets = {}

    def needs_reconfiguration(self, step_cnt):
        return True

    def configure_connection(self, connection: AbstractConnection):
        # dict<int, list<str>>
        commands_per_node = defaultdict(list)
        check_commands_per_node = defaultdict(list)

        for emulation_node_x, emulation_node_y, interface_x, interface_y in (
                (connection.emulation_node_x, connection.emulation_node_y, connection.interface_x, connection.interface_y),
                (connection.emulation_node_y, connection.emulation_node_x, connection.interface_y, connection.interface_x),
        ):

            (emulation_node_1, interface_1), (emulation_node_2, interface_2) = sorted(
                [(emulation_node_x, interface_x), (emulation_node_y, interface_y)])
            # use same subnet for connection from both sides
            key = emulation_node_1._id, emulation_node_2._id

            is_new_subnet = True
            # for each connection remember the subnet
            if key in self.used_subnets:
                is_new_subnet = False
                subnet = self.used_subnets[key]
            else:
                # new subnet -> remember
                subnet = next(self.subnet_generator)
                self.used_subnets[key] = subnet

            # new subnet -> 0, else 1
            idx_ip = int(not is_new_subnet)

            # get ip addresses
            ip = self.get_ip(subnet, offset=idx_ip)

            # Ticket #81
            idx_iface = self.get_interface_index_fun(emulation_node_x, interface_x)
            ip_set_command_up = self.get_ip_addr_change_cmd(self.get_nic_name(idx_iface), ip, subnet.netmask)
            commands_per_node[emulation_node_x].append(ip_set_command_up)

            ping_cmd = self.connectivity_checker_fun(ip, self.network_timeout)
            # my peer must be able to ping me
            check_commands_per_node[emulation_node_y].append(ping_cmd)

        return commands_per_node, check_commands_per_node

    def get_ip(self, subnet, offset=0):
        # skip net address (+1)
        ip_addr = subnet[1 + offset]
        return ip_addr
