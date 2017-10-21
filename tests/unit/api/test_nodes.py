from collections import OrderedDict
from unittest.mock import MagicMock

import pytest

from miniworld import singletons


class TestNodes:
    @pytest.fixture
    def mock_nodes(self):
        node = MagicMock()
        node.virtualization_layer.__class__.__name__ = 'Qemu'
        interface = MagicMock()
        interface.get_mac.return_value = '00:00:00:00:00:01'
        interface.node_class = 2
        interface.node_class_name = "mesh"
        node.interfaces = [interface]
        singletons.simulation_manager.nodes_id_mapping = {
            1: node,
        }

    def test_node(self, client, mock_nodes):
        res = client.execute('''
        query {
           nodes {
               id
               virtualization
               interfaces {
                   mac
               }
           }
        }
        ''')
        assert res == {'data': OrderedDict([('nodes', [OrderedDict(
            [('id', 1), ('virtualization', 'Qemu'), ('interfaces', [OrderedDict([('mac', '00:00:00:00:00:01')])])])])])}

    def test_node_filter(self, client, mock_nodes):
        res = client.execute('''
        query {
           nodes(id: 1) {
               id
               virtualization
               interfaces {
                   nodeClass
                   nodeClassName
                   mac
               }
           }
        }
        ''')
        assert res == {'data': OrderedDict([('nodes', [OrderedDict([('id', 1), ('virtualization', 'Qemu'), (
            'interfaces',
            [OrderedDict([('nodeClass', 2), ('nodeClassName', 'mesh'), ('mac', '00:00:00:00:00:01')])])])])])}
