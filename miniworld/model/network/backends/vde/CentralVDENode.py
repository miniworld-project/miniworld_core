import miniworld.model.network.backends.vde.VDEConstants
from miniworld import log
from miniworld.model.emulation.nodes.virtual import CentralNode
from miniworld.model.network.backends.vde import VDESwitch

class CentralVDENode(CentralNode.CentralNode):

    # TODO: #54,#55
    def start(self, switch = False):
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
        log.info("starting management node/switch ...")
        super(CentralVDENode, self)._start(switch=switch)

        # we want all nodes connected -> disable color patch
        log.info("disabling color patch for %s", self.__class__.__name__)
        self.switch.colorful = False

        # TODO: #54,#55: only for network backend "vde"
        # color tap/management device
        if self.switch.colorful:
            log.info("coloring management tap device ...")
            self.switch.color_interface(port =miniworld.model.network.backends.vde.VDEConstants.PORT_MANAGEMENT, color = self.interface.node_class)

        log.info("associating management tap device with management vlan ...")
        # associate tap/management device with management vlan
        self.switch.move_interface_to_vlan(self.interface, port =miniworld.model.network.backends.vde.VDEConstants.PORT_MANAGEMENT)

        self.after_pre_shell_commands()