import pytest
from sqlalchemy.orm.exc import NoResultFound

from miniworld.model.interface.Interface import Interface
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.service.persistence.connections import ConnectionPersistenceService


class TestConnectionPersistenceService:
    @pytest.fixture
    def service(self) -> ConnectionPersistenceService:
        return ConnectionPersistenceService()

    def test_add(self, service, connections):
        # check that obj is persisted and start by 0 hack is working
        assert service.get(connection_id=0)._id == 0

        # domain model got updated
        assert connections[0]._id == 0

    def test_delete(self, service, connections):
        service.delete()
        with pytest.raises(NoResultFound):
            service.get(connection_id=connections[0].id)

    def test_get(self, connections, service: ConnectionPersistenceService):
        assert service.get(connection_id=connections[0]._id)._id == 0

    def test_exists(self, connections, service: ConnectionPersistenceService):
        assert service.exists(node_x_id=0, node_y_id=1)

    def test_update_impairment(self, connections, service: ConnectionPersistenceService):
        id = connections[0]._id
        service.update_impairment(id, {'loss': 0.5})

        assert service.get(connection_id=id).impairment == {'loss': 0.5}

    def test_update_state(self, connections, service: ConnectionPersistenceService):
        id = connections[0]._id
        service.update_state(id, False)

        assert service.get(connection_id=id).connected is False

    @pytest.mark.parametrize('connections', [1], indirect=True)
    def test_all(self, connections, service: ConnectionPersistenceService):
        res = service.all()
        connection = res[0]
        assert isinstance(connection.emulation_node_x, EmulationNode)
        assert isinstance(connection.emulation_node_y, EmulationNode)
        assert isinstance(connection.interface_x, Interface)
        assert isinstance(connection.interface_y, Interface)
