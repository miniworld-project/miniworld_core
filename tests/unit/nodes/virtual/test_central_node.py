from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.virtual.CentralNode import CentralNode
from miniworld.singletons import singletons


class TestCentralNode:
    def test_interfaces(self):
        node = CentralNode(singletons.network_backend_bootstrapper)
        assert len(node.network_mixin.interfaces) == 1
        assert node.connection_type == AbstractConnection.ConnectionType.central
