
from miniworld import log
from miniworld.model.emulation.nodes.virtual.ManagementNode import ManagementNode
from miniworld.model.network.backends.vde.VDEConstants import PORT_MANAGEMENT
from miniworld.Config import config
from miniworld.model.network.interface import Interfaces
from miniworld.model.network.interface.Interface import Management


class ManagementNodeVDE(ManagementNode):

    def __init__(self, network_backend):
        interfaces = Interfaces.Interfaces.factory([Management])
        id = config.get_bridge_tap_name()
        super(ManagementNode, self).__init__(id, network_backend, interfaces)

    def _start(self, switch=True, bridge_dev_name=None):
        '''
        1. Start hub/switch
        2. Color interfaces (if switch wants so)
        3. Move interface to VLAN

        Parameters
        ----------
        switch : bool, optional (default is True)

        Raises
        ------
        NetworkManagementSwitchBridgeNotExisting
        '''

        if bridge_dev_name is None:
            bridge_dev_name = config.get_bridge_tap_name()

        log.info("starting management node/switch ...")
        super(ManagementNodeVDE, self)._start(switch=switch, bridge_dev_name=bridge_dev_name)

        # start and wait for switches
        #self.switch.start(bridge_dev_name = self.bridge_name, switch = switch)

        # color tap/management device
        self.switch.color_interface(PORT_MANAGEMENT, self.interface.node_class)

        log.info("associating management tap device with management vlan ...")
        # associate tap/management device with management vlan
        self.switch.move_interface_to_vlan(self.interface, PORT_MANAGEMENT)

        self.after_pre_shell_commands()
        # TODO: Ticket:48
