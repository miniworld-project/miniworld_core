from typing import List
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm.exc import NoResultFound

from miniworld.model.db.base import Connection, Node
from miniworld.model.interface.Interface import Interface
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.service.persistence.connections import ConnectionPersistenceService
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.singletons import singletons


class TestConnectionPersistenceService:
    @pytest.fixture
    def service(self) -> ConnectionPersistenceService:
        return ConnectionPersistenceService()

    @pytest.fixture
    def connections(self, request, service) -> List[Connection]:
        conns = []
        singletons.config.is_management_switch_enabled = MagicMock(return_value=False)
        for x in range(getattr(request, 'param', 3)):
            # TODO: move to nodes
            network_backend_bootstrapper = singletons.network_backend_bootstrapper_factory.get()
            i = Interfaces.factory_from_interface_names(['mesh'])[0]
            i.mac = i.get_mac(x * 2)
            i2 = Interfaces.factory_from_interface_names(['mesh'])[0]
            i2.mac = i2.get_mac(x * 2 + 1)
            n = EmulationNode(network_backend_bootstrapper, [i])
            n2 = EmulationNode(network_backend_bootstrapper, [i2])

            conn = AbstractConnection(n, n2, i, i2)
            service.add(conn)
            # check that the correct autoincrement start value is used
            assert conn._id == x
            NodePersistenceService().add(Node.from_domain(n))
            NodePersistenceService().add(Node.from_domain(n2))
            conns.append(conn)

        singletons.network_manager.connections = {conn._id: conn for conn in conns}
        return conns

    def test_add(self, service, connections):
        assert service.get(connections[0]._id).step_added == singletons.simulation_manager.current_step

    def test_delete(self, service, connections):
        service.delete()
        with pytest.raises(NoResultFound):
            service.get(connections[0].id)

    def test_get(self, connections, service: ConnectionPersistenceService):
        assert service.get(connections[0]._id).id == 0

    def test_exists(self, connections, service: ConnectionPersistenceService):
        assert service.exists(node_x_id=0, node_y_id=1)

    def test_update_impairment(self, connections, service: ConnectionPersistenceService):
        id = connections[0]._id
        service.update_impairment(id, {'loss': 0.5})

        assert service.get(id).impairment == {'loss': 0.5}

    def test_update_state(self, connections, service: ConnectionPersistenceService):
        id = connections[0]._id
        service.update_state(id, False)

        assert service.get(id).active is False

    @pytest.mark.parametrize('connections', [1], indirect=True)
    def test_all(self, connections, service: ConnectionPersistenceService):
        res = service.all()
        connection = res[0]
        assert isinstance(connection.emulation_node_x, EmulationNode)
        assert isinstance(connection.emulation_node_y, EmulationNode)
        assert isinstance(connection.interface_x, Interface)
        assert isinstance(connection.interface_y, Interface)
