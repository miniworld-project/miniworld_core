import base64
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm.exc import NoResultFound

from miniworld.singletons import singletons


class TestNodes:
    @staticmethod
    def get_id(id: int) -> str:
        return base64.b64encode('EmulationNode:{}'.format(id).encode()).decode()

    def test_node_get(self, client, mock_nodes, snapshot):
        res = client.execute('''
        query getNode($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''', variable_values={'id': self.get_id(0)})
        snapshot.assert_match(res)

    def test_node_get_nonexisting(self, client, mock_nodes, snapshot, monkeypatch):
        monkeypatch.setattr('miniworld.service.persistence.nodes.NodePersistenceService.get', MagicMock(side_effect=NoResultFound))

        res = client.execute('''
        query getNode($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''', variable_values={'id': self.get_id(0)})
        snapshot.assert_match(res)

    def test_node_interfaces(self, client, mock_nodes, snapshot):
        res = client.execute('''
        {
          emulationNodes {
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
    def test_node_distances(self, client, mock_nodes, mock_distances, snapshot):
        res = client.execute('''
        {
          emulationNodes {
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

    def test_node_execute_command(self, client, monkeypatch):
        result = "bin\nboot"
        monkeypatch.setattr('miniworld.singletons.network_backend_bootstrapper.emulation_service.exec_node_cmd', MagicMock(return_value=result))
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
