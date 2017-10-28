class TestWebServer:
    def test_ping(self, client):
        res = client.execute('''
        query {
            ping
        }
        ''')
        assert res['data'] == {
            "ping": "pong"
        }
