import json
import sys
from typing import Dict, List
from unittest.mock import MagicMock

import pytest
from graphene.test import Client

import miniworld
from miniworld.api.webserver import schema
from miniworld.model.domain.connection import Connection
from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.service.emulation.interface import InterfaceService
from miniworld.singletons import singletons


@pytest.fixture(autouse=True)
def fresh_env():
    miniworld.init(do_init_db=False)
    singletons.network_backend_bootstrapper = singletons.network_backend_bootstrapper_factory.get()


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
def mock_nodes(request, mock_persistence, monkeypatch) -> Dict[int, Node]:
    interface_service = InterfaceService()

    def get_interface(interface_id):
        for emulation_node in singletons.simulation_manager.nodes_id_mapping.values():
            for interface in emulation_node._node.interfaces:
                if interface._id == interface_id:
                    return interface

    interface_id_counter = 0
    node_id_counter = 0
    if mock_persistence:
        get = MagicMock(side_effect=get_interface)
        monkeypatch.setattr('miniworld.service.persistence.interfaces.InterfacePersistenceService.get', get)

    def configure_net(interface, node):
        nonlocal interface_id_counter
        interface.ipv4 = str(interface_service.get_ip(node_id=node._id, interface=interface))
        interface.mac = interface_service.get_mac(node_id=node._id, interface=interface)
        interface._id = interface_id_counter
        interface_id_counter += 1

    cnt_nodes = getattr(request, 'param', None) or 2
    for i in range(cnt_nodes):
        interface = InterfaceService.factory(['mesh'])[0]
        emulation_node = MagicMock()
        emulation_node._node = n = Node(_id=node_id_counter, interfaces=[interface], type=AbstractConnection.ConnectionType.user)
        node_id_counter += 1
        for interface in n.interfaces:
            configure_net(interface, n)
        singletons.simulation_manager.nodes_id_mapping[i] = emulation_node

    if mock_persistence:
        get = MagicMock(side_effect=lambda node_id: singletons.simulation_manager.nodes_id_mapping.get(node_id))
        monkeypatch.setattr('miniworld.service.persistence.nodes.NodePersistenceService.get', get)
        monkeypatch.setattr('miniworld.service.persistence.nodes.NodePersistenceService.all', MagicMock(return_value=singletons.simulation_manager.nodes_id_mapping.values()))

    return singletons.simulation_manager.nodes_id_mapping


@pytest.fixture
def mock_connections(mock_nodes, mock_persistence, monkeypatch) -> List[AbstractConnection]:
    """ Connect nodes pair-wise. """

    connections = []
    for idx, (node1, node2) in enumerate(zip(mock_nodes.values(), list(mock_nodes.values())[1:])):
        link_quality_dict = {
            'bandwidth': 500,
            'loss': 0.5
        }
        interface1 = node1.interfaces[0]
        interface2 = node2.interfaces[0]
        conn = Connection(
            _id=idx,
            emulation_node_x=node1,
            emulation_node_y=node2,
            interface_x=interface1,
            interface_y=interface2,
            connection_type=AbstractConnection.ConnectionType.user,
            is_remote_conn=False,
            impairment=link_quality_dict,
            connected=True,
            step_added=0,
            distance=10,
        )
        connections.append(conn)
        # TODO: is this ensured for functional tests too?
        if node1._node.connections is None:
            node1._node.connections = []
        if node2._node.connections is None:
            node2._node.connections = []
        node1._node.connections.append(conn)

    connections = {conn._id: conn for conn in connections}
    if mock_persistence:
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.all', MagicMock(return_value=connections))
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.get', MagicMock(side_effect=lambda connection_id: connections.get(connection_id)))

    return connections


@pytest.fixture
def mock_distances():
    singletons.simulation_manager.movement_director = MagicMock()
    singletons.simulation_manager.movement_director.get_distances_from_nodes.return_value = {(0, 1): 1, (0, 2): -1,
                                                                                             (1, 2): 1}
