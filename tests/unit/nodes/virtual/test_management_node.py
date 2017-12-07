from miniworld.network.connection import AbstractConnection
from miniworld.nodes.virtual.ManagementNode import ManagementNode
from miniworld.singletons import singletons


class TestManagementNode:
    def test_interfaces(self):
        node = ManagementNode(singletons.network_backend_bootstrapper)
        assert len(node.network_mixin.interfaces) == 1
        assert node.connection_type == AbstractConnection.ConnectionType.mgmt
