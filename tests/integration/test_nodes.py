import pytest

from miniworld.service.persistence.nodes import NodePersistenceService


class TestNodePersistenceService:
    @pytest.fixture
    def service(self):
        return NodePersistenceService()

    def test_add(self, service, connections):
        assert service.get(0)._id == 0

    def test_exists(self, service, connections):
        assert service.exists(connections[0].emulation_node_x._id)

    def test_get(self, service, connections):
        emulation_node = service.get(node_id=0)
        assert emulation_node._id == 0
        assert len(emulation_node.interfaces) == 2
        assert emulation_node.interfaces[0]._id == 0
        assert emulation_node.interfaces[1]._id == 1

        assert len(emulation_node.connections) == 1
        assert emulation_node.connections[0]._id == 0
