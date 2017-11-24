import pytest

from miniworld.model.db.base import Connection, Node, Interface
from miniworld.service.persistence.connections import ConnectionPersistenceService


class TestConnectionPersistenceService:
    @pytest.fixture
    def service(self):
        return ConnectionPersistenceService()

    def test_to_domain(self, service: ConnectionPersistenceService, mock_nodes, mock_connections):
        connection = mock_connections[0]  # type: AbstractConnection
        db_connection = Connection(id=0)
        db_connection.node_x = Node(id=connection.emulation_node_x._id)
        db_connection.node_y = Node(id=connection.emulation_node_y._id)
        db_connection.interface_x = Interface(id=connection.interface_x._id)
        db_connection.interface_y = Interface(id=connection.interface_y._id)

        abstract_connection = service.to_domain(db_connection)
        assert abstract_connection.interface_x._id == connection.interface_x._id
        assert abstract_connection.interface_y._id == connection.interface_y._id
        assert abstract_connection.emulation_node_x._id == connection.emulation_node_x._id
        assert abstract_connection.emulation_node_y._id == connection.emulation_node_y._id
