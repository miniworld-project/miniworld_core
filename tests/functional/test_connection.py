class TestConnection:
    def test_connection_get(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "Q29ubmVjdGlvbjowCg==") {
            ... on Connection {
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
        }
        ''')
        snapshot.assert_match(res)

    def test_connection_get_nonexisting(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "Q29ubmVjdGlvbjoxMDAwMAo=") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_links(self, client, snapshot):
        res = client.execute('''
        {
            connections {
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
