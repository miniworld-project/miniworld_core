import base64
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm.exc import NoResultFound


class TestNodes:
    @staticmethod
    def get_id(id: int) -> str:
        return base64.b64encode('Connection:{}'.format(id).encode()).decode()

    def test_connection_get(self, client, mock_nodes, mock_connections, snapshot):
        res = client.execute('''
        query getConnection($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }''', variable_values={'id': self.get_id(0)})
        snapshot.assert_match(res)

    def test_connection_get_nonexisting(self, client, mock_nodes, mock_connections, snapshot, monkeypatch):
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.get', MagicMock(side_effect=NoResultFound))

        res = client.execute('''
        query getConnection($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''', variable_values={'id': self.get_id(1000000)})
        snapshot.assert_match(res)

    def test_connections(self, client, mock_nodes, mock_connections, snapshot):
        res = client.execute('''
        {
          connections {
            iid
            kind
            impairment
            connected
            distance
            emulationNodeX { iid kind }
            interfaceX { iid }
            emulationNodeY{ iid kind }
            interfaceY { iid }
          }
        }''')
        snapshot.assert_match(res)

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_node_links(self, client, mock_nodes, mock_connections, snapshot, monkeypatch):
        def get_connection(connection_id):
            return mock_connections[connection_id]

        mock = MagicMock(side_effect=get_connection)
        monkeypatch.setattr('miniworld.service.persistence.connections.ConnectionPersistenceService.get', mock)
        res = client.execute('''
        {
            connections(connected: true) {
                id
                iid
                kind
                impairment
                connected
                distance
                emulationNodeX { iid kind }
                emulationNodeY { iid kind }
                interfaceX { iid }
                interfaceY { iid }
          }
        }
        ''')
        snapshot.assert_match(res)
