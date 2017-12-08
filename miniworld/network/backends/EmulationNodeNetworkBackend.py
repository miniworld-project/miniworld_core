from io import StringIO

from miniworld.network.backends.NetworkMixin import NetworkMixin
from miniworld.service.emulation.interface import InterfaceService
from miniworld.singletons import singletons
from miniworld.util import NetUtil
from miniworld.model.domain.interface import Interface

__author__ = 'Nils Schmidt'


def get_cmd_rename_mgmt_interface():
    # TODO: #63: generic solution? works only if image has iproute2 installed :/
    CMD_RENAME_MANAGEMENT_INTERFACE = """
# name management interface
last_eth=$(ls -1 /sys/class/net/|grep {iface_prefix}|tail -n 1)
ip link set name {mgmt_iface} $last_eth
ifconfig {mgmt_iface} up
""".format(mgmt_iface=singletons.config.get_bridge_tap_name(),
           iface_prefix=singletons.scenario_config.get_network_links_nic_prefix())

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
        self._logger = singletons.logger_factory.get_logger(self)
        super(EmulationNodeNetworkBackend, self).__init__(network_backend_bootstrapper)

        self._interface_service = InterfaceService()
        self.node_id = node_id

        self.nlog = singletons.logger_factory.get_node_logger(self.node_id)

        self.interfaces = interfaces or []

        if management_switch:
            self.interfaces.append(self._interface_service.factory([Interface.InterfaceType.management])[0])

            # TODO: REMOVE
            # let the management interface be the last one
            self.interfaces = list(sorted(self.interfaces, key=lambda interface: interface.class_id))

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
        if singletons.config.is_management_switch_enabled():
            emulation_node.virtualization_layer.run_commands_eager(StringIO(get_cmd_rename_mgmt_interface()))
            self.nic_mgmt_ipv4_config(emulation_node)

        self.nic_ipv4_config(emulation_node)

    #########################################
    # Network Config
    #########################################

    def _nic_mgmt_ipv4_config(self, emulation_node):
        for _if in [interface for interface in self.interfaces if interface.name == Interface.InterfaceType.management.value]:
            ip = self._interface_service.get_ip(node_id=emulation_node._id, interface=_if)
            _if.ipv4 = str(ip)
            netmask = self._interface_service.get_netmask(interface=_if)
            # TODO: #63: we dont know if renaming worked, therefore try to rename both ethX and mgmt
            cmd_ip_change = NetUtil.get_ip_addr_change_cmd(singletons.config.get_bridge_tap_name(), ip, netmask)
            emulation_node.virtualization_layer.run_commands_eager(StringIO(cmd_ip_change))

    def nic_ipv4_config(self, emulation_node):
        pass

    def nic_mgmt_ipv4_config(self, emulation_node):
        self._nic_mgmt_ipv4_config(emulation_node)
