import pytest


class TestMobility:
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
                        "id": 0,
                        "links": [
                            {
                                "distance": 1.0,
                                "node": {
                                    "id": 1
                                }
                            },
                            {
                                "distance": -1.0,
                                "node": {
                                    "id": 2
                                }
                            }
                        ]
                    }
                },
                {
                    "node": {
                        "id": 1,
                        "links": [
                            {
                                "distance": 1.0,
                                "node": {
                                    "id": 2
                                }
                            }
                        ]
                    }
                }
            ]
        }

    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_distances_filter_between(self, client, mock_nodes, mock_distances):
        res = client.execute('''
        query {
           distances(id: 0, between: {min: 0, max:1}) {
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
                        "id": 0,
                        "links": [
                            {
                                "distance": 1.0,
                                "node": {
                                    "id": 1
                                }
                            }
                        ]
                    }
                }
            ]
        }
