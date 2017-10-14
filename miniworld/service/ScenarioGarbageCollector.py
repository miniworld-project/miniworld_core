from collections import defaultdict

from miniworld.singletons import singletons

KEY_SINGLETON = "singleton"
KEY_OBJECT = "object"


class ScenarioGarbageCollector(defaultdict):
    """ Ensures that singletons and objects created during a scenario are cleared
     correctly such that no state of a scenario is kept. """

    def __init__(self):
        super(ScenarioGarbageCollector, self).__init__(list)
        self._logger = singletons.logger_factory.get_logger(self)

    # required to grab a logger for self
    def __hash__(self):
        return id(self)

    def add_singleton(self, singleton_class):
        self._logger.debug("adding %s to resettable singletons with simulation state", singleton_class)
        if singleton_class not in self[KEY_SINGLETON]:
            self[KEY_SINGLETON].append(singleton_class)

    def add_object(self, obj):
        # NOTE: str() might have unitialized variables
        self._logger.debug("adding tmp %s to resettable objects with simulation state", type(obj))
        if obj not in self[KEY_OBJECT]:
            self[KEY_OBJECT].append(obj)

    def reset_simulation_scenario_state(self):
        self._logger.info("resetting simulation_scenario_state")
        # objects may require singletons, hence first garbage collect objects
        for obj in self[KEY_OBJECT]:
            self._logger.debug("resetting '{!r}'".format(obj))
            try:
                obj.reset()
            except NotImplementedError:
                self._logger.critical("Object '%s@%s' did not implement the reset() method!", obj, obj.__class__)
            except Exception as e:
                if singletons.config.is_log_cleanup():
                    self._logger.exception(e)

        for singleton in self[KEY_SINGLETON]:
            self._logger.debug("resetting '{!r}'".format(singleton))
            try:
                singleton.reset()
            except Exception as e:
                if singletons.config.is_log_cleanup():
                    self._logger.exception(e)

        self._logger.info("clearing simulate state objects ...")
        self[KEY_OBJECT] = []
