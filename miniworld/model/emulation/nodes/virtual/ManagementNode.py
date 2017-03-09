import sys

from miniworld.model.emulation.nodes.virtual.VirtualNode import VirtualNode
from miniworld.model.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.model.network.interface import Interfaces
from miniworld.model.network.interface.Interface import Management
from miniworld.Config import config

__author__ = 'Nils Schmidt'

# TODO: DOC  Ticket 34#
MANAGEMENT_NODE_ID = sys.maxint

class ManagementNode(VirtualNode):
    '''
    A `VirtualNode` whose hub/switch is colored.
    The link quality of its connections are not influenced by the distance matrix.
    No link quality adjustment is done. This is intended for management stuff.
    '''
    def __init__(self, network_backend_bootstrapper, id=None):
        if id is None:
            id = MANAGEMENT_NODE_ID
        interfaces = Interfaces.Interfaces.factory([Management])
        super(ManagementNode, self).__init__(id, network_backend_bootstrapper, interfaces)

    def _start(self, switch = True, bridge_dev_name=None):
        super(ManagementNode, self)._start(switch=switch, bridge_dev_name = bridge_dev_name)

    def init_connection_info(self):
        '''

        Returns
        -------
        ConnectionInfo
        '''
        return ConnectionInfo(is_mgmt=True)

# TODO: USE .__class__ in BridgedNode!

def is_management_node(node):
    return isinstance(node, ManagementNode)
