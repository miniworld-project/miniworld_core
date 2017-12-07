from miniworld.network.connection import ConnectionServiceBase
from miniworld.singletons import singletons


class TestConnectionService:
    def test_reset(self):
        reset_called = False

        class Sub(ConnectionServiceBase):
            def reset(self):
                nonlocal reset_called
                reset_called = True

        Sub()
        # call reset
        singletons.simulation_state_gc.reset_simulation_scenario_state()
        # check that the object could clean up it's state
        assert reset_called
