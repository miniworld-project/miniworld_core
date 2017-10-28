from collections import OrderedDict

import pytest


class TestNodes:
    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_distances(self, client, mock_nodes, mock_distances):
        res = client.execute('''
        query {
           distances {
               node {
                   id
                   links {
                       node { id }
                       distance
                   }
               }
           }
        }
        ''')
        assert res['data'] == {
            "distances": [
                {
                    "node": {
                        "id": 1,
                        "links": [
                            {
                                "distance": 1.0,
                                "node": {
                                    "id": 2
                                }
                            },
                            {
                                "distance": -1.0,
                                "node": {
                                    "id": 3
                                }
                            }
                        ]
                    }
                },
                {
                    "node": {
                        "id": 2,
                        "links": [
                            {
                                "distance": 1.0,
                                "node": {
                                    "id": 3
                                }
                            }
                        ]
                    }
                }
            ]
        }

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_distances_filter(self, client, mock_nodes, mock_distances):
        res = client.execute('''
        query {
           distances(id: 1) {
               node {
                   id
                   links {
                       node { id }
                       distance
                   }
               }
           }
        }
        ''')
        assert res == {'data': OrderedDict([('distances', [OrderedDict([('node', OrderedDict([('id', 1), ('links', [OrderedDict([('node', OrderedDict([('id', 2)])), ('distance', 1.0)]), OrderedDict([('node', OrderedDict([('id', 3)])), ('distance', -1.0)])])]))])])])}

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_distances_filter_between(self, client, mock_nodes, mock_distances):
        res = client.execute('''
        query {
           distances(id: 1, between: {min: 0, max:1}) {
               node {
                   id
                   links {
                       node { id }
                       distance
                   }
               }
           }
        }
        ''')
        assert res == {'data': OrderedDict([('distances', [OrderedDict([('node', OrderedDict([('id', 1), ('links', [OrderedDict([('node', OrderedDict([('id', 2)])), ('distance', 1.0)])])]))])])])}
