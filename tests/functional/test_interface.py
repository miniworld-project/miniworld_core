class TestInterface:
    def test_interface_get(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "SW50ZXJmYWNlOjAK") {
            id
            ... on Interface {
              iid
              id
              name
              mac
              ipv4
              nrHostInterface
            }
          }
        }
        ''')
        snapshot.assert_match(res)

    def test_interface_get_non_existing(self, client, snapshot):
        res = client.execute('''
        {
          node(id: "SW50ZXJmYWNlOjEwMDAwCg==") {
            id
            ... on InternalIdentifier {
              iid
            }
          }
        }
        ''')
        snapshot.assert_match(res)
