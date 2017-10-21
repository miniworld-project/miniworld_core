import json
from collections import OrderedDict
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
        assert res['data'] == OrderedDict([('scenarioStart', OrderedDict([('scenarioConfig', '{"foo": "bar"}')]))])

    def test_step(self, client):
        res = client.execute('''
        mutation {
            scenarioStep(steps:1) {
                steps
            }
        }
        ''')
        print(res.data['scenarioStep'])
