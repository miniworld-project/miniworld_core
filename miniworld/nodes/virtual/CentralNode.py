from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.nodes.virtual import VirtualNode


class CentralNode(VirtualNode.VirtualNode):
    """
    A VirtualNode whose links are quality adjusted by distance matrix.
    """

    def __init__(self, node: Node):
        super(CentralNode, self).__init__(node=node)
        self.connection_type = AbstractConnection.ConnectionType.central

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        return ConnectionInfo(connection_type=AbstractConnection.ConnectionType.central)

    @staticmethod
    def is_central_node_interface(interface: str):
        return interface == Interface.InterfaceType.hub.value

    @staticmethod
    def is_central_node(node):
        return isinstance(node, CentralNode)
