from pprint import pformat

from miniworld.config.Scenario import ScenarioConfig
from miniworld.singletons import singletons


class MovementDirectorFactory:
    TOPOLOGY_MODE_MANUAL = "manual"
    TOPOLOGY_MODE_CORE = "core"
    TOPOLOGY_MODE_ARMA = "arma"
    TOPOLOGY_MODE_DEFAULT = "default"
    TOPOLOGY_MODE_NO_MOBILITY = "no_mobility"

    def __init__(self):
        self._logger = singletons.logger_factory.get_logger(self)

    def get(self, cnt_nodes):
        from miniworld.mobility.MovementDirectorNoMobility import MovementDirectorNoMobility

        walk_model_name = singletons.scenario_config.get_walk_model_name()
        if walk_model_name is None:
            topology_mode = self.TOPOLOGY_MODE_NO_MOBILITY

        else:
            if walk_model_name == ScenarioConfig.WALK_MODEL_NAME_ARMA:
                topology_mode = self.TOPOLOGY_MODE_ARMA
            elif walk_model_name == ScenarioConfig.WALK_MODEL_NAME_CORE:
                topology_mode = self.TOPOLOGY_MODE_CORE
            else:
                topology_mode = self.TOPOLOGY_MODE_DEFAULT

        if topology_mode == self.TOPOLOGY_MODE_CORE:
            # late import: imports modules that need the MiniWorld working directory being created
            from miniworld.mobility import MovementDirectorCoreConfig

            core_scenarios = singletons.scenario_config.get_core_scenarios()
            self._logger.info("using topology provided by core scenario configs '%s'", pformat(core_scenarios))
            movement_director = MovementDirectorCoreConfig.MovementDirectorCoreConfig(core_scenarios)

        elif topology_mode == self.TOPOLOGY_MODE_ARMA:
            from miniworld.mobility.MovementDirectorArma import MovementDirectorArma
            arma_filepath = singletons.scenario_config.get_walk_model_arma_filepath()
            movement_director = MovementDirectorArma(cnt_nodes, arma_filepath)
            # TODO: change in none hardcoded string
            movement_director.set_path_to_replay_file(arma_filepath)
            raise NotImplementedError

        elif topology_mode == self.TOPOLOGY_MODE_DEFAULT:
            from miniworld.mobility.MovementDirector import MovementDirector
            movement_director = MovementDirector({
                singletons.scenario_config.get_walk_model_name(): cnt_nodes}
            )  # , ("MoveOnBigStreets", 20)])#MovementDirector({"RandomWalk" : cnt_nodes})
        elif topology_mode == self.TOPOLOGY_MODE_NO_MOBILITY:
            movement_director = MovementDirectorNoMobility()
        else:
            raise ValueError("Topology mode is unknown!")

        self._logger.info("created MovementDirector '%s' ...", movement_director)
        return movement_director
