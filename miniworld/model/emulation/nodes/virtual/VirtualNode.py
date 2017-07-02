from miniworld import log
from miniworld.Config import config
from miniworld.model.emulation.nodes.EmulationNode import EmulationNode
from miniworld.model.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.model.singletons.Singletons import singletons


class VirtualNode(EmulationNode):
    '''
    This class in contrast to an `EmulationNode`is virtual in the sense of not being backed by a qemu instance.
    This virtual node is used to have a custom hub/switch while still  being able to use existing node which requires an `EmulationNode`.

    Attributes
    ----------
    interface : Interface
    switch : AbstractSwitch
    bridge_name : str
    '''

    # TODO: RENAME BRIDGE_NAME
    def __init__(self, node_id, network_backend_bootstrapper, interfaces = None):
        '''

        Parameters
        ----------
        node_id : int

        network_backend_bootstrapper : NetworkBackendBootStrapper
        interfaces : Interfaces
        '''

        # TODO: #82: network_backend is of type NetworkBackendEmulationNode
        # this call inits the interfaces of the :py:class:`.NetworkBackend`

        network_mixin=network_backend_bootstrapper.virtual_node_network_backend_type(network_backend_bootstrapper, node_id, interfaces=interfaces,
                           management_switch=config.is_management_switch_enabled())
        super(VirtualNode, self).__init__(node_id, network_backend_bootstrapper, interfaces = interfaces,
                                            network_mixin=network_mixin)

        self.interface = self.network_mixin.interfaces[0]
        self.switch = None

    def _start(self, bridge_dev_name = None, switch = None):
        '''

        Parameters
        ----------
        bridge_dev_name : str, optional (default is not bridged at all)
        switch

        Returns
        -------

        '''

        self.network_mixin.start(bridge_dev_name = bridge_dev_name, switch = switch)
        self.switch = next(iter(self.network_mixin.switches.values()))

    def init_connection_info(self):
        '''

        Returns
        -------
        ConnectionInfo
        '''
        raise NotImplementedError

    # TODO: #82: DOC
    def connect_to_emu_node(self, network_backend, emulation_node):
        ''' Helper function to connect the virtual node to an `EmulationNode`.

        Parameters
        ----------
        network_backend
        emulation_node

        Returns
        -------
        AbstractSwitch, AbstractConnection, Interface, Interface
            The connection between the nodes and the two interfaces
        '''
        interface = self.interface
        log.info("connecting '%s' to '%s' ...", emulation_node, self)


        # get the interface with the same type
        emu_node_if = emulation_node.network_mixin.interfaces.filter_type(type(interface))[0]

        connection_info = self.init_connection_info()
        # NetworkBackendNotifications
        connected, switch, connection = singletons.network_manager.before_link_initial_start(network_backend, self,
                                                                                     emulation_node, interface,
                                                                                     emu_node_if, connection_info, start_activated=True)
        singletons.network_manager.after_link_initial_start(connected, switch, connection, network_backend, self,
                                                            emulation_node, interface, emu_node_if, connection_info,
                                                            start_activated=True)

        return switch, connection, interface, emu_node_if


    #########################################
    ### Disable shell stuff
    #########################################

    # TODO: #54,#55: adjust doc
    def run_pre_network_shell_commands(self, flo_post_boot_script, *args, **kwargs):
        pass

    # TODO: #54,#55: adjust doc
    def run_post_network_shell_commands(self, *args, **kwargs):
        pass