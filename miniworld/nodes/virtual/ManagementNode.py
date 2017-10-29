from miniworld.model.interface import Interfaces
from miniworld.model.interface.Interface import Management
from miniworld.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.nodes.virtual.VirtualNode import VirtualNode

__author__ = 'Nils Schmidt'


class ManagementNode(VirtualNode):
    """
    A `VirtualNode` whose hub/switch is colored.
    The link quality of its connections are not influenced by the distance matrix.
    No link quality adjustment is done. This is intended for management stuff.
    """

    def __init__(self, network_backend_bootstrapper):
        interfaces = Interfaces.Interfaces.factory([Management])
        super(ManagementNode, self).__init__(network_backend_bootstrapper, interfaces)

    def _start(self, switch=True, bridge_dev_name=None):
        super(ManagementNode, self)._start(switch=switch, bridge_dev_name=bridge_dev_name)

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        return ConnectionInfo(is_mgmt=True)

    @staticmethod
    def is_management_node(node):
        return isinstance(node, ManagementNode)
