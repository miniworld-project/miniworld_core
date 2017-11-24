from miniworld.model.interface import Interfaces
from miniworld.model.interface.Interface import HubWiFi
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.nodes.virtual import VirtualNode


class CentralNode(VirtualNode.VirtualNode):
    """
    A VirtualNode whose links are quality adjusted by distance matrix.
    """

    def __init__(self, network_backend_bootstrapper):
        """

        Parameters
        ----------
        network_backend_bootstrapper : NetworkBackendBootStrapper
        id : int, optional (default is generated)
        bridge_name : str
        """
        interfaces = Interfaces.Interfaces.factory([HubWiFi])

        super(CentralNode, self).__init__(network_backend_bootstrapper, interfaces=interfaces)

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        return ConnectionInfo(connection_type=AbstractConnection.ConnectionType.central)

    # TODO: REMOVE ?
    # @staticmethod
    # def is_bridge_node_id(node_id):
    #     return CentralNode.gen_bridge_node_id() <= node_id < ManagementNode.MANAGEMENT_NODE_ID

    @staticmethod
    def is_central_node_interface(interface):
        return isinstance(interface, HubWiFi)

    @staticmethod
    def is_central_node(node):
        return isinstance(node, CentralNode)
