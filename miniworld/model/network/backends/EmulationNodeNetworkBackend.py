from io import StringIO

from miniworld import config
from miniworld.Scenario import scenario_config
from miniworld.log import get_node_logger
from miniworld.model.network.backends.NetworkMixin import NetworkMixin
from miniworld.model.network.interface import Interfaces, Interface
from miniworld.util import NetUtil

__author__ = 'Nils Schmidt'


def get_cmd_rename_mgmt_interface():
    # TODO: #63: generic solution? works only if image has iproute2 installed :/
    CMD_RENAME_MANAGEMENT_INTERFACE = """
# name management interface
last_eth=$(ls -1 /sys/class/net/|grep {iface_prefix}|tail -n 1)
ip link set name {mgmt_iface} $last_eth
ifconfig {mgmt_iface} up
""".format(mgmt_iface=config.get_bridge_tap_name(), iface_prefix=scenario_config.get_network_links_nic_prefix())

    return CMD_RENAME_MANAGEMENT_INTERFACE


class EmulationNodeNetworkBackend(NetworkMixin):
    """
    This class enables each :py:class:`.EmulationNode` to handle network backend stuff differently by encapsulating these methods into an extra class.

    For example the base :py:class:`.NetworkBackendEmulationNode`.

    Attributes
    ----------
    network_backend_boot_strapper : NetworkBackendBootStrapper
    """

    def __init__(self, network_backend_bootstrapper, node_id,
                 # network
                 interfaces=None, management_switch=False):
        super(EmulationNodeNetworkBackend, self).__init__(network_backend_bootstrapper)

        self.node_id = node_id

        self.nlog = get_node_logger(self.node_id)

        if interfaces is None:
            self.interfaces = Interfaces.Interfaces.factory([Interface.Mesh])
        else:
            self.interfaces = interfaces

        if management_switch:
            self.interfaces.append(Interfaces.Interfaces.factory([Interface.Management])[0])

        # let the management interface be the last one
        self.interfaces.sort()

    def _start(self, *args, **kwargs):
        pass

    def reset(self):
        pass

    #############################################################
    # EmulationNode notifications
    #############################################################

    # TODO: DOC
    def after_pre_shell_commands(self, emulation_node):
        pass

    def do_network_config_after_pre_shell_commands(self, emulation_node):
        # Rename Management Interface and set ip
        if config.is_management_switch_enabled():
            emulation_node.virtualization_layer.run_commands_eager(StringIO(get_cmd_rename_mgmt_interface()))
            self.nic_mgmt_ipv4_config(emulation_node)

        self.nic_ipv4_config(emulation_node)

    #########################################
    # Network Config
    #########################################

    # TODO: DOC, sublcass methods

    def _nic_ipv4_config(self, emulation_node):
        for _if in self.interfaces.filter_normal_interfaces():
            idx = self.interfaces.index(_if)
            ip = _if.get_ip(emulation_node.id)
            netmask = _if.get_netmask()

            cmd_ip_change = NetUtil.get_ip_addr_change_cmd(
                "%s%s" % (scenario_config.get_network_links_nic_prefix(), idx),
                ip, netmask)
            emulation_node.virtualization_layer.run_commands_eager(StringIO(cmd_ip_change))

    def _nic_mgmt_ipv4_config(self, emulation_node):
        for _if in self.interfaces.filter_mgmt():
            ip = _if.get_ip(emulation_node.id)
            netmask = _if.get_netmask()
            # TODO: #63: we dont know if renaming worked, therefore try to rename both ethX and mgmt
            cmd_ip_change = NetUtil.get_ip_addr_change_cmd(config.get_bridge_tap_name(), ip, netmask)
            emulation_node.virtualization_layer.run_commands_eager(StringIO(cmd_ip_change))

    def nic_ipv4_config(self, emulation_node):
        pass

    def nic_mgmt_ipv4_config(self, emulation_node):
        self._nic_mgmt_ipv4_config(emulation_node)
