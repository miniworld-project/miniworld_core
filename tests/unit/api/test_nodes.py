class TestNodes:
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
        assert res == {
            "data": {
                "nodes": [
                    {
                        "id": 1,
                        "interfaces": [
                            {
                                "mac": "02:01:00:00:00:01"
                            },
                            {
                                "mac": "0a:01:00:00:00:01"
                            }
                        ],
                        "virtualization": "QemuTap"
                    },
                    {
                        "id": 2,
                        "interfaces": [
                            {
                                "mac": "02:01:00:00:00:02"
                            },
                            {
                                "mac": "0a:01:00:00:00:02"
                            }
                        ],
                        "virtualization": "QemuTap"
                    }
                ]
            }
        }

    def test_node_filter(self, client, mock_nodes):
        res = client.execute('''
        query {
           nodes(id: 1) {
               id
               virtualization
               interfaces {
                   id
                   name
                   mac
               }
           }
        }
        ''')
        assert res == {
            "data": {
                "nodes": [
                    {
                        "id": 1,
                        "interfaces": [
                            {
                                "id": 0,
                                "mac": "02:01:00:00:00:01",
                                "name": "mesh"
                            },
                            {
                                "id": 1,
                                "mac": "0a:01:00:00:00:01",
                                "name": "management"
                            }
                        ],
                        "virtualization": "QemuTap"
                    }
                ]
            }
        }
