import pytest

import miniworld
from miniworld.service.persistence.connections import ConnectionPersistenceService
from miniworld.service.persistence.nodes import NodePersistenceService
from tests.unit.conftest import fresh_env, mock_connections, mock_nodes, mock_distances  # noqa


@pytest.fixture(autouse=True)  # noqa
def db_fresh_env(fresh_env):
    miniworld.init_db()

    return True


@pytest.fixture
def mock_persistence():
    return False


@pytest.fixture  # noqa
def connections(mock_connections):
    connection = mock_connections[0]  # type: AbstractConnection
    node_0 = connection.emulation_node_x
    node_1 = connection.emulation_node_y
    node_persistence_service = NodePersistenceService()
    node_persistence_service.add(node_0)
    node_persistence_service.add(node_1)
    connection_persistence_service = ConnectionPersistenceService()
    connection_persistence_service.add(connection)

    return mock_connections
