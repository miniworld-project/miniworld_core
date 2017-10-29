import pytest


class TestImpairment:
    @pytest.mark.parametrize('mock_nodes', [3], indirect=True)
    def test_impairments(self, client, mock_nodes, mock_connections):
        res = client.execute('''
        query {
            impairments {
                node {
                    id
                    links {
                        node { id }
                        interface { name }
                        impairment
                    }
                }
            }
        }
        ''')
        assert res['data'] == {
            "impairments": [
                {
                    "node": {
                        "id": 0,
                        "links": [
                            {
                                "impairment": {
                                    "bandwidth": 500,
                                    "loss": 0.5
                                },
                                "interface": {
                                    "name": "mesh"
                                },
                                "node": {
                                    "id": 1
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
                                "impairment": {
                                    "bandwidth": 500,
                                    "loss": 0.5
                                },
                                "interface": {
                                    "name": "mesh"
                                },
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
    def test_impairments_filter_id_active(self, client, mock_nodes, mock_connections):
        res = client.execute('''
        query {
            impairments(id: 1, active: true) {
                node {
                    id
                    links {
                        node { id }
                        interface { name }
                        impairment
                    }
                }
            }
        }
        ''')
        assert res['data'] == {
            "impairments": [
                {
                    "node": {
                        "id": 1,
                        "links": [
                            {
                                "impairment": {
                                    "bandwidth": 500,
                                    "loss": 0.5
                                },
                                "interface": {
                                    "name": "mesh"
                                },
                                "node": {
                                    "id": 2
                                }
                            }
                        ]
                    }
                }
            ]
        }
