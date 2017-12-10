from collections import OrderedDict

from miniworld.model.domain.node import Node
from miniworld.nodes import AbstractNode
from miniworld.singletons import singletons


class VirtualNode(AbstractNode):
    """
    This class in contrast to an `EmulationNode`is virtual in the sense of not being backed by a qemu instance.
    This virtual node is used to have a custom hub/switch while still  being able to use existing node which requires an `EmulationNode`.

    Attributes
    ----------
    interface : Interface
    switch : AbstractSwitch
    bridge_name : str
    """

    # TODO: RENAME BRIDGE_NAME
    def __init__(self, node: Node):
        super().__init__(node=node)

        # TODO: #82: network_backend is of type NetworkBackendEmulationNode
        # this call inits the interfaces of the :py:class:`.NetworkBackend`
        self.network_backend_bootstrapper = singletons.network_backend_bootstrapper

        self.interface = self._node.interfaces[0]
        self.switch = None
        self.switches = None
        self.create_switches()

    def create_switches(self):
        # create one switch for each node interface
        self.switches = OrderedDict(
            (_if, self.network_backend_bootstrapper.switch_type(self._node._id, _if)) for _if in self._node.interfaces
        )

    def start_switches(self, *args, **kwargs):
        for switch in self.switches.values():
            switch.start(*args, **kwargs)

    def _start(self, bridge_dev_name=None, switch=None):
        """

        Parameters
        ----------
        bridge_dev_name : str, optional (default is not bridged at all)
        switch

        Returns
        -------

        """

        self.switch = next(iter(self.switches.values()))
        self.start_switches(switch=switch, bridge_dev_name=bridge_dev_name)

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        raise NotImplementedError

    # TODO: #82: DOC
    def connect_to_emu_node(self, network_backend, emulation_node):
        """ Helper function to connect the virtual node to an `EmulationNode`.

        Parameters
        ----------
        network_backend
        emulation_node

        Returns
        -------
        AbstractSwitch, AbstractConnection, Interface, Interface
            The connection between the nodes and the two interfaces
        """
        interface = self.interface
        self._logger.info("connecting '%s' to '%s' ...", emulation_node, self)

        # get the interface with the same type
        emu_node_if = [iface for iface in emulation_node._node.interfaces if iface.name == interface.name][0]

        connection_info = self.init_connection_info()
        # NetworkBackendNotifications
        connected, switch, connection = singletons.network_manager.before_link_initial_start(network_backend, self,
                                                                                             emulation_node, interface,
                                                                                             emu_node_if,
                                                                                             connection_info,
                                                                                             start_activated=True)
        singletons.network_manager.after_link_initial_start(connected, switch, connection, network_backend, self,
                                                            emulation_node, interface, emu_node_if, connection_info,
                                                            start_activated=True)

        return switch, connection, interface, emu_node_if
