from unittest.mock import MagicMock

import pytest

from miniworld.singletons import singletons


# TODO: test get non existent id
class TestNodes:
    def test_node_get(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  node(id: "RW11bGF0aW9uTm9kZTow") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_node_get_nonexisting(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  node(id: "RW11bGF0aW9uTm9kZToxMDAwMAo=") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_connection_get(self, client, mock_nodes, mock_connections, snapshot):
        res = client.execute('''
{
  node(id: "Q29ubmVjdGlvbjowCg==") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_connection_get_nonexisting(self, client, mock_nodes, mock_connections, snapshot):
        res = client.execute('''
{
  node(id: "Q29ubmVjdGlvbjoxMDAwMAo=") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_interface_get(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  node(id: "SW50ZXJmYWNlOjAK") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_interface_get_non_existing(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  node(id: "SW50ZXJmYWNlOjEwMDAwCg==") {
    id
    ... on InternalIdentifier {
      iid
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_node_id_filter(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  emulationNodes(iid:0) {
    id
    iid
  }
}
        ''')
        snapshot.assert_match(res)

    def test_node_interfaces(self, client, mock_nodes, snapshot):
        res = client.execute('''
{
  emulationNodes(kind: "user") {
    id
    iid
    virtualization
    interfaces {
      edges {
        node {
          id
          iid
          name
          mac
          ipv4
          kind
        }
      }
    }
  }
}
        ''')
        snapshot.assert_match(res)

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_node_links(self, client, mock_nodes, mock_connections, snapshot, monkeypatch):
        def get_connection(connection_id):
            return mock_connections[connection_id]

        mock = MagicMock(side_effect=get_connection)
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.get', mock)
        res = client.execute('''
{
  emulationNodes(kind: "user") {
    iid
    virtualization
    links(connected: true) {
      edges {
        node {
          id
          iid
          impairment
          connected
          kind
          this {
            interface {iid}
          }
          other {
            interface {iid}
            emulationNode {iid}
          }
        }
      }
    }
  }
}
        ''')
        snapshot.assert_match(res)

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_node_distances(self, client, mock_nodes, mock_distances, snapshot):
        res = client.execute('''
{
  emulationNodes(kind: "user") {
    iid
    distances(between:{min: 0}) {
      edges {
        node {
          distance
          emulationNode {
            id
            iid
          }
        }
      }
    }
  }
}
        ''')
        snapshot.assert_match(res)

    def test_node_execute_command(self, client):
        result = "bin\nboot"
        singletons.simulation_manager.exec_node_cmd = MagicMock(return_value=result)
        res = client.execute('''
mutation ($nodeID: Int, $cmd: String, $validate: Boolean, $timeout: Float) {
   nodeExecuteCommand(id: $nodeID, cmd: $cmd, validate: $validate, timeout: $timeout) {
       result
   }
}
        ''', variable_values={
            "nodeID": 0,
            "cmd": "ls -1 /",
            "validate": True,
            "timeout": 1.0,
        })
        assert res['data']['nodeExecuteCommand'] == {
            "result": result
        }
