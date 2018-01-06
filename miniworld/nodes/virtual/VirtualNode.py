from miniworld.model.domain.node import Node
from miniworld.nodes import AbstractNode
from miniworld.singletons import singletons


class VirtualNode(AbstractNode):
    """
    This class in contrast to an `EmulationNode`is virtual in the sense of not being backed by a qemu instance.
    This virtual node is used to have a custom hub/switch while still  being able to use existing node which requires an `EmulationNode`.
    """

    # TODO: RENAME BRIDGE_NAME
    def __init__(self, node: Node = None):
        super().__init__(node=node)

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        raise NotImplementedError

    # TODO: #82: DOC
    def connect_to_emu_node(self, virtual_node: Node, real_node: Node):
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
        self._logger.info("connecting '%s' to '%s' ...", virtual_node, real_node)

        # get the interface with the same type
        virtual_node_if = virtual_node.interfaces[0]
        real_node_if = [iface for iface in real_node.interfaces if iface.name == virtual_node_if.name][0]

        connection_info = self.init_connection_info()
        # NetworkBackendNotifications
        connected, switch, connection = singletons.network_manager.before_link_initial_start(
            singletons.network_backend,
            virtual_node,
            real_node,
            virtual_node_if,
            real_node_if,
            connection_info,
            start_activated=True
        )
        singletons.network_manager.after_link_initial_start(
            connected,
            switch,
            connection,
            singletons.network_backend,
            virtual_node,
            real_node,
            virtual_node_if,
            real_node_if,
            connection_info,
            start_activated=True
        )

        return switch, connection, virtual_node_if, real_node_if
