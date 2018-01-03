import base64
from unittest.mock import MagicMock

from sqlalchemy.orm.exc import NoResultFound


class TestNodes:
    @staticmethod
    def get_id(id: int) -> str:
        return base64.b64encode('Interface:{}'.format(id).encode()).decode()

    def test_interface_get(self, client, mock_nodes, snapshot):
        res = client.execute('''
        query getInterface($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''', variable_values={'id': self.get_id(0)})
        snapshot.assert_match(res)

    def test_interface_get_non_existing(self, client, mock_nodes, snapshot, monkeypatch):
        monkeypatch.setattr('miniworld.service.persistence.interfaces.InterfacePersistenceService.get', MagicMock(side_effect=NoResultFound))

        res = client.execute('''
        query getInterface($id: ID!) {
          node(id: $id) {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''', variable_values={'id': self.get_id(10000000)})
        snapshot.assert_match(res)
