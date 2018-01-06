import json
from unittest.mock import Mock

from miniworld import singletons


class TestScenario:
    def test_start(self, client):
        singletons.simulation_manager = Mock()
        res = client.execute('''
        mutation MyMutations($scenario_config: String) {
            scenarioStart(scenarioConfig: $scenario_config) {
                scenarioConfig
            }
        }
        ''', variable_values={'scenario_config': json.dumps({"foo": "bar"})})
        assert res['data'] == {
            "scenarioStart": {
                "scenarioConfig": "{\"foo\": \"bar\"}"
            }
        }

    def test_step(self, client):
        singletons.simulation_manager = Mock()
        res = client.execute('''
        mutation MyMutations {
            scenarioStep(steps:1) {
                steps
            }
        }
        ''')
        assert res['data'] == {
            "scenarioStep": {
                "steps": 1
            }
        }

    def test_abort(self, client):
        singletons.simulation_manager = Mock()
        client.execute('''
        mutation MyMutations {
            scenarioAbort {status}
        }
        ''')
