class TestNodes:
    def test_node(self, client, mock_nodes):
        res = client.execute('''
        query {
           nodes {
               id
           }
        }
        ''')
        assert res['data'] == {
            "nodes": [
                {
                    "id": 0,
                },
                {
                    "id": 1,
                }
            ]
        }

    def test_node_filter(self, client, mock_nodes):
        res = client.execute('''
        query {
           nodes(id: 0) {
               id
               virtualization
               interfaces {
                   id
                   name
                   mac
                   ipv4
               }
           }
        }
        ''')
        assert res['data'] == {
            "nodes": [
                {
                    "id": 0,
                    "interfaces": [
                        {
                            "id": 0,
                            "ipv4": "10.0.1.1",
                            "mac": "02:01:00:00:00:00",
                            "name": "mesh"
                        },
                        {
                            "id": 1,
                            "ipv4": "172.21.0.1",
                            "mac": "0a:01:00:00:00:00",
                            "name": "management"
                        }
                    ],
                    "virtualization": "QemuTap"
                }
            ]
        }
