class TestNode:
    def test_node_get(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "RW11bGF0aW9uTm9kZTow") {
            id
            ... on EmulationNode {
              id
              iid
              virtualization
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_node_get_nonexisting(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "RW11bGF0aW9uTm9kZToxMDAwMAo=") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_nodes(self, client, snapshot):
        res = client.execute('''
        {
          emulationNodes {
            id
            iid
            kind
            virtualization
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_interfaces(self, client, snapshot):
        res = client.execute('''
        {
          emulationNodes {
            id
            iid
            kind
            virtualization
            interfaces {
              edges {
                node {
                  iid
                  id
                  name
                  mac
                  ipv4
                  nrHostInterface
                }
              }
            }
          }
        }
        ''')
        snapshot.assert_match(res)
