from unittest.mock import MagicMock

from miniworld.model.connections.ConnectionStore import ConnectionStore
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode


class TestConnectionStore:
    def test_get_link_quality_matrix(self):
        network_backend_bootstrapper = MagicMock()
        conn_store = ConnectionStore()
        link_quality_dict = {
            'bandwidth': 500,
            'loss': 0.5
        }
        i = Interfaces.factory_from_interface_names(['mesh'])[0]
        i2 = Interfaces.factory_from_interface_names(['mesh'])[0]
        n = EmulationNode(1, network_backend_bootstrapper, i)
        n2 = EmulationNode(2, network_backend_bootstrapper, i2)

        conn = AbstractConnection(n, n2, i, i2)
        conn_store.add_connection(conn, active=True,
                                  link_quality_dict=link_quality_dict)
        print(conn_store.get_link_quality_matrix(include_interfaces=False).to_json())
