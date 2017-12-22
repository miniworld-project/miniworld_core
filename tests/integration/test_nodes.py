import pytest

from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.service.persistence.nodes import NodePersistenceService


class TestNodePersistenceService:
    @pytest.fixture
    def service(self):
        return NodePersistenceService()

    def test_add_2_interfaces(self, service):
        node = Node(
            interfaces=[
                Interface(name='mesh', nr_host_interface=0),
                Interface(name='mesh', nr_host_interface=1),
            ]
        )
        service.add(node)
        node = service.get(node_id=0)

        assert node._id == 0
        assert node.interfaces[0]._id == 0
        assert node.interfaces[1]._id == 1

    def test_add(self, service, connections):
        emulation_node = service.get(node_id=0)

        # test that domain IDs got updated
        node_0 = connections[0].emulation_node_x._node
        assert node_0._id == 0
        assert node_0.interfaces[0]._id == 0

        # node and interface persisted and start by 0 hack is working
        assert emulation_node._id == 0
        assert emulation_node.interfaces[0]._id == 0

    def test_exists(self, service, connections):
        assert service.exists(connections[0].emulation_node_x._id)

    def test_get(self, service, connections):
        emulation_node = service.get(node_id=0)
        assert emulation_node._id == 0
        assert len(emulation_node.interfaces) == 2
        assert emulation_node.interfaces[0]._id == 0
        assert emulation_node.interfaces[1]._id == 1
