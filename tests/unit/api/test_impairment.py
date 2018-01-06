import pytest

from miniworld.impairment.bridged.Range import Range
from miniworld.singletons import singletons


class TestImpairment:
    @pytest.fixture
    def mock_impairment(self):
        singletons.simulation_manager.impairment = Range()

    def test_impairment(self, client, mock_impairment):
        res = client.execute('''
        query {
            impairment {
                initial {
                    connected
                    settings
                }
                requested {
                    connected
                    settings
                }
                maxConnected
            }
        }
        ''')
        assert res['data'] == {
            "impairment": {
                "initial": {
                    "connected": False,
                    "settings": {
                        "bandwidth": None,
                        "loss": 0
                    }
                },
                "maxConnected": 30,
                "requested": None
            }
        }

    def test_impairment_by_distance(self, client, mock_impairment):
        res = client.execute('''
        query {
            impairment(distance: 10) {
                initial {
                    connected
                    settings
                }
                requested {
                    connected
                    settings
                }
                maxConnected
            }
        }
        ''')
        assert res['data'] == {
            "impairment": {
                "initial": {
                    "connected": False,
                    "settings": {
                        "bandwidth": None,
                        "loss": 0
                    }
                },
                "maxConnected": 30,
                "requested": {
                    "connected": True,
                    "settings": {
                        "loss": 0
                    }
                }
            }
        }
