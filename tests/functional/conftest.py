import pytest
import sys
from graphqlclient import GraphQLClient, json
from typing import Dict


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
