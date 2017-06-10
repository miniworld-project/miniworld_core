from collections import OrderedDict

import miniworld.model.network.backends.vde.VDEConstants
from miniworld.Scenario import scenario_config
from miniworld.model import StartableObject
from miniworld.model.network.backends.SwitchMixin import SwitchMixin
from miniworld.model.network.backends.vde import VDESwitch
from miniworld.model.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
__author__ = 'Nils Schmidt'


class EmulationNodeNetworkBackendVDE(EmulationNodeNetworkBackend, SwitchMixin):

    def __init__(self, network_backend_bootstrapper, node_id,
              # network
              interfaces = None, management_switch = False):
        super(EmulationNodeNetworkBackendVDE, self).__init__(network_backend_bootstrapper, node_id, interfaces = interfaces, management_switch = management_switch)

        self.create_switches()

    def _start(self, *args, **kwargs):
        self.start_switches()

    def after_pre_shell_commands(self, emulation_node):
        '''
        1. Set switch size
        2. Color interfaces
        3. Move interfaces to specific VLAN
        '''

        # NOTE: uds socket has to be reachable!

        self.set_switch_sizes()

        self.color_interfaces()
        self.nlog.info("coloring interfaces ...")
        self.move_interfaces_to_vlan()

    # TODO: MOVE TO VDESWITCH
    def color_interfaces(self):
        '''
        Color all interfaces, therefore simulate a hop-2-hop network.
        '''
        self.nlog.info("coloring qemu vde_switch port ...")

        for _if, vde_switch in self.switches.items():
            self.nlog.debug("coloring %s, %s", _if, vde_switch)
            vde_switch.color_interface(port=miniworld.model.network.backends.vde.VDEConstants.PORT_QEMU, color=_if.node_class)


    def move_interfaces_to_vlan(self):
        # move the interfaces to their corresponding vlan
        for _if, vde_switch in self.switches.items():
            vde_switch.move_interface_to_vlan(port=miniworld.model.network.backends.vde.VDEConstants.PORT_QEMU, interface=_if)

    def set_switch_sizes(self):
        ''' Set the size of the switch '''
        for vde_switch in self.switches.values():
            vde_switch.set_port_size(scenario_config.get_network_backend_vde_num_ports())

