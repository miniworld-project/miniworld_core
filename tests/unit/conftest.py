import json
import sys
from copy import deepcopy
from typing import Dict, List
from unittest.mock import MagicMock

import pytest
from graphene.test import Client

import miniworld
from miniworld.api.webserver import schema
from miniworld.model.base import Base
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.singletons import singletons


@pytest.fixture(autouse=True)
def fresh_env():
    miniworld.init(do_init_db=False)
    # make domain model IDs predictable
    old_counter = deepcopy(Base.counter)
    yield
    # restore old counter
    Base.counter = old_counter


@pytest.fixture(autouse=True)
def mock_db(fresh_env):
    singletons.db_session = MagicMock()


class GraphQLError(Exception):
    pass


@pytest.fixture
def client():
    client = Client(schema)
    old_execute = client.execute

    def new_execute(*args, **kwargs):
        res = old_execute(*args, **kwargs)
        if res.get('errors') is not None:
            raise GraphQLError(res['errors'])

        # print json in the same structure as we can assert it in tests later
        print(json.dumps(res['data'], indent=2))

        sys.stderr.flush()
        return res

    client.execute = new_execute
    return client


@pytest.fixture
def mock_persistence():
    return True


@pytest.fixture
def mock_nodes(request, mock_persistence, monkeypatch) -> Dict[int, EmulationNode]:
    def get_interface(interface_id):
        for emulation_node in singletons.simulation_manager.nodes_id_mapping.values():
            for interface in emulation_node.network_mixin.interfaces:
                if interface._id == interface_id:
                    return interface
    interface_id_counter = 0
    if mock_persistence:
        get = MagicMock(side_effect=get_interface)
        monkeypatch.setattr('miniworld.service.persistence.interfaces.InterfacePersistenceService.get', get)

    def configure_net(interface, node):
        nonlocal interface_id_counter
        interface.ipv4 = interface.get_ip(node._id)
        interface.ipv6 = interface.get_ip(node._id)
        interface.mac = interface.get_mac(node._id)
        interface._id = interface_id_counter
        interface_id_counter += 1

    cnt_nodes = getattr(request, 'param', None) or 2
    network_backend_bootstrapper = singletons.network_backend_bootstrapper
    for i in range(cnt_nodes):
        interface = Interfaces.factory_from_interface_names(['mesh'])[0]
        n = EmulationNode(network_backend_bootstrapper, [interface])
        for interface in n.network_mixin.interfaces:
            configure_net(interface, n)
        singletons.simulation_manager.nodes_id_mapping[i] = n

    if mock_persistence:
        get = MagicMock(side_effect=lambda node_id: singletons.simulation_manager.nodes_id_mapping.get(node_id))
        monkeypatch.setattr('miniworld.service.persistence.nodes.NodePersistenceService.get', get)

    return singletons.simulation_manager.nodes_id_mapping


@pytest.fixture
def mock_connections(mock_nodes, mock_persistence, monkeypatch) -> List[AbstractConnection]:
    """ Connect nodes pair-wise. """

    abstract_connections = []
    for idx, (node1, node2) in enumerate(zip(mock_nodes.values(), list(mock_nodes.values())[1:])):
        link_quality_dict = {
            'bandwidth': 500,
            'loss': 0.5
        }
        interface1 = node1.network_mixin.interfaces[0]
        interface2 = node2.network_mixin.interfaces[0]
        conn = AbstractConnection(node1, node2, interface1, interface2, _id=idx, impairment=link_quality_dict, connected=True, step_added=0, distance=10)
        abstract_connections.append(conn)

    singletons.network_manager.connections = {conn._id: conn for conn in abstract_connections}
    if mock_persistence:
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.all', MagicMock(return_value=abstract_connections))
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.get', MagicMock(side_effect=lambda connection_id: singletons.network_manager.connections.get(connection_id)))

    return abstract_connections


@pytest.fixture
def mock_distances():
    singletons.simulation_manager.movement_director = MagicMock()
    singletons.simulation_manager.movement_director.get_distances_from_nodes.return_value = {(0, 1): 1, (0, 2): -1,
                                                                                             (1, 2): 1}
