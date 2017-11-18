import pytest

from miniworld.model.db.base import Node
from miniworld.service.persistence.nodes import NodePersistenceService


class TestNodePersistenceService:
    @pytest.fixture
    def service(self):
        return NodePersistenceService()

    @pytest.fixture
    def nodes(self, service):
        return [service.add(
            Node(
                id=1,
                interfaces=[],
            )
        )]

    def test_add(self, service, nodes):
        pass

    def test_exists(self, service, nodes):
        assert service.exists(nodes[0].id)
