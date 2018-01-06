from miniworld import singletons
from miniworld.config.Config import GlobalConfig


class TestConfig:
    def test_instance(self):
        assert isinstance(singletons.config, GlobalConfig)
