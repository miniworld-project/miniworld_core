from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.nodes.virtual.VirtualNode import VirtualNode

__author__ = 'Nils Schmidt'


class ManagementNode(VirtualNode):
    """
    A `VirtualNode` whose hub/switch is colored.
    The link quality of its connections are not influenced by the distance matrix.
    No link quality adjustment is done. This is intended for management stuff.
    """

    def __init__(self, node: Node):
        super(ManagementNode, self).__init__(node=node)
        self.connection_type = AbstractConnection.ConnectionType.mgmt

    def start(self, switch=True, bridge_dev_name=None):
        super(ManagementNode, self).start(switch=switch, bridge_dev_name=bridge_dev_name)

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        return ConnectionInfo(connection_type=AbstractConnection.ConnectionType.mgmt)

    @staticmethod
    def is_management_node(node):
        return isinstance(node, ManagementNode)
