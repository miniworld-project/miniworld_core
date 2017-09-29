
from miniworld.model.emulation.nodes.virtual import ManagementNode
from miniworld.model.emulation.nodes.virtual import VirtualNode
from miniworld.model.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.model.network.interface import Interfaces
from miniworld.model.network.interface.Interface import HubWiFi


class CentralNode(VirtualNode.VirtualNode):
    """
    A VirtualNode whose links are quality adjusted by distance matrix.
    """

    cnt_instances = 0

    def __init__(self, network_backend_bootstrapper, id=None):
        """

        Parameters
        ----------
        network_backend_bootstrapper : NetworkBackendBootStrapper
        id : int, optional (default is generated)
        bridge_name : str
        """
        interfaces = Interfaces.Interfaces.factory([HubWiFi])
        if id is None:
            id = self.gen_bridge_node_id()

        super(CentralNode, self).__init__(id, network_backend_bootstrapper, interfaces=interfaces)
        CentralNode.cnt_instances += 1

    def init_connection_info(self):
        """

        Returns
        -------
        ConnectionInfo
        """
        return ConnectionInfo(is_central=True)

    # TODO: REMOVE ?
    # @staticmethod
    # def is_bridge_node_id(node_id):
    #     return CentralNode.gen_bridge_node_id() <= node_id < ManagementNode.MANAGEMENT_NODE_ID

    # TODO: CHANGE NAME
    @staticmethod
    def gen_bridge_node_id():
        return ManagementNode.MANAGEMENT_NODE_ID - CentralNode.cnt_instances - 1


def is_central_node_interface(interface):
    return isinstance(interface, HubWiFi)


def is_central_node(node):
    return isinstance(node, CentralNode)
