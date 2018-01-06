import sys
from typing import Dict

import pytest
from graphqlclient import GraphQLClient, json

import miniworld
from miniworld.model.db.base import Interface, Node, Connection
from miniworld.network.connection import AbstractConnection
from miniworld.singletons import singletons


@pytest.fixture(autouse=True)
def fresh_env():
    miniworld.init(do_init_db=True)


def assert_topologies_equal(t1, t2):
    """ Compare topologies but ignore order inside value list """
    assert t1.keys() == t2.keys()

    t1s, t2s = {}, {}
    for key in t1.keys():
        # convert values to sets to compare so that order does not matter
        t1s[key] = set(t1[key])
        t2s[key] = set(t2[key])

    assert t1s == t2s


@pytest.fixture
def client():
    client = GraphQLClient('http://127.0.0.1:5000/graphql')
    client_execute = client.execute

    def execute_graphql(query, *args, **kwargs) -> Dict:
        """ Monkey-patch execute method of GraphQLClient. """
        print('executing graphql: {}, variables: {}'.format(query, kwargs.get('variables')), file=sys.stderr)
        res_json = client_execute(query, *args, **kwargs)
        res = json.loads(res_json)
        if res.get('errors') is not None:
            print('graphql errors: {}'.format(res['errors']), file=sys.stderr)
            sys.exit(1)
        print(res_json, file=sys.stderr)
        return res

    client.execute = execute_graphql
    return client


@pytest.fixture(autouse=True)
def setup_db(fresh_env):
    """ Set up a sample database with the following network topology:
    1 <-> 2 <-> 3
    """
    with singletons.db_session.session_scope() as session:

        node_0 = Node(
            id=0,
            type=AbstractConnection.ConnectionType.user,
        )
        node_1 = Node(
            id=1,
            type=AbstractConnection.ConnectionType.user,
        )
        node_2 = Node(
            id=2,
            type=AbstractConnection.ConnectionType.user,
        )
        nodes = [node_0, node_1, node_2]

        interface_0 = Interface(
            id=0,
            name='mesh',
            nr_host_interface=0,
            ipv4='172.16.0.1',
            mac='00:00:00:00:00:01',
            node_id=node_0.id,
        )
        interface_1 = Interface(
            id=1,
            name='mesh',
            nr_host_interface=0,
            ipv4='172.16.0.2',
            mac='00:00:00:00:00:02',
            node_id=node_1.id,
        )
        interface_2 = Interface(
            id=2,
            name='mesh',
            nr_host_interface=0,
            ipv4='172.16.0.3',
            mac='00:00:00:00:00:03',
            node_id=node_2.id,
        )
        interfaces = [interface_0, interface_1, interface_2]

        # node_0 <-> node_1
        connection_0 = Connection(
            id=0,
            node_x_id=node_0.id,
            node_y_id=node_1.id,
            interface_x=interface_0,
            interface_y=interface_1,
            type=AbstractConnection.ConnectionType.user,
            impairment={'loss': 100},
            connected=True,
            step_added=0,
            distance=10,
        )

        # node_1 <-> node_2
        connection_1 = Connection(
            id=1,
            node_x_id=node_1.id,
            node_y_id=node_2.id,
            interface_x=interface_1,
            interface_y=interface_2,
            type=AbstractConnection.ConnectionType.user,
            impairment={'loss': 50},
            connected=True,
            step_added=0,
            distance=5,
        )
        connections = [connection_0, connection_1]

        for interface in interfaces:
            session.add(interface)
        for node in nodes:
            session.add(node)
        for connection in connections:
            session.add(connection)
