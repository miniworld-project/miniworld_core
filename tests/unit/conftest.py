import json
import sys
from typing import Dict
from unittest.mock import MagicMock

import pytest
from copy import deepcopy
from graphene.test import Client

import miniworld
from miniworld.model.base import Base
from miniworld.api.webserver import schema
from miniworld.model.connections.ConnectionDetails import ConnectionDetails
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.nodes.EmulationNodes import EmulationNodes
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
        print(json.dumps(res['data'], indent=4, sort_keys=True)
              .replace('null', 'None')
              .replace('false', 'False')
              .replace('true', 'True'), file=sys.stderr)

        sys.stderr.flush()
        return res

    client.execute = new_execute
    return client


@pytest.fixture
def mock_nodes(request) -> Dict[int, EmulationNode]:
    def configure_net(interface, node):
        interface.ipv4 = interface.get_ip(node._id)
        interface.ipv6 = interface.get_ip(node._id)
        interface.mac = interface.get_mac(node._id)

    cnt_nodes = getattr(request, 'param', None) or 2
    network_backend_bootstrapper = singletons.network_backend_bootstrapper_factory.get()
    for i in range(cnt_nodes):
        interface = Interfaces.factory_from_interface_names(['mesh'])[0]
        n = EmulationNode(network_backend_bootstrapper, [interface])
        for interface in n.interfaces:
            configure_net(interface, n)
        singletons.simulation_manager.nodes_id_mapping[i] = n

    return singletons.simulation_manager.nodes_id_mapping


@pytest.fixture
def mock_connections(mock_nodes):
    """ Connect nodes pair-wise. """

    connections = {}
    for node1, node2 in zip(mock_nodes.values(), list(mock_nodes.values())[1:]):
        link_quality_dict = {
            'bandwidth': 500,
            'loss': 0.5
        }
        interface1 = node1.interfaces[0]
        interface2 = node2.interfaces[0]
        conn = AbstractConnection(node1, node2, interface1, interface2)
        connection_details = ConnectionDetails(conn, link_quality_dict)
        connections[node1] = [(EmulationNodes([node1, node2]), Interfaces([interface1, interface2]), connection_details)]

    # only return active connections
    def get_connections(node, active):
        return connections.get(node, []) if active else []

    singletons.network_manager.connection_store.get_connections = MagicMock(side_effect=get_connections)


@pytest.fixture
def mock_distances():
    singletons.simulation_manager.movement_director = MagicMock()
    singletons.simulation_manager.movement_director.get_distances_from_nodes.return_value = {(0, 1): 1, (0, 2): -1,
                                                                                             (1, 2): 1}
