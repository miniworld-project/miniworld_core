from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.nodes.virtual.CentralNode import CentralNode


class TestCentralNode:
    def test_interfaces(self):
        node = CentralNode(Node(interfaces=[Interface()]))
        assert len(node._node.interfaces) == 1
        assert node.connection_type == AbstractConnection.ConnectionType.central
