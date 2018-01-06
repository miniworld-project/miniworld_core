from miniworld import singletons
from miniworld.config.Scenario import ScenarioConfig


class TestScenarioConfig:
    def test_instance(self):
        assert isinstance(singletons.scenario_config, ScenarioConfig)
