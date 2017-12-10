from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.nodes.virtual.ManagementNode import ManagementNode


class TestManagementNode:
    def test_interfaces(self):
        node = ManagementNode(Node(interfaces=[Interface()]))
        assert len(node._node.interfaces) == 1
        assert node.connection_type == AbstractConnection.ConnectionType.mgmt
