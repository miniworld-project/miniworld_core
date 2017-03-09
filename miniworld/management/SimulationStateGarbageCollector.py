from collections import defaultdict

from miniworld import log, singletons

KEY_SINGLETON = "singleton"
KEY_OBJECT = "object"


class SimulationStateGarbageCollector(defaultdict):

    def __init__(self):
        super(SimulationStateGarbageCollector, self).__init__(list)

    # TODO: #55: REMOVE from this class
    def add_singleton_with_simulation_scenario_state_(self, singleton_class):
        log.debug("adding %s to resettable singletons with simulation state", singleton_class)
        if not singleton_class in self[KEY_SINGLETON]:
            self[KEY_SINGLETON].append(singleton_class)

    def add_tmp_object_with_simulation_scenario_state(self, obj):
        # NOTE: str() might have unitialized variables
        log.debug("adding tmp %s to resettable objects with simulation state", type(obj))
        #if not obj in self[KEY_OBJECT]:
        self[KEY_OBJECT].append(obj)

    def reset_simulation_scenario_state(self):
        from miniworld import log
        log.info("resetting simulation_scenario_state")
        for singleton in self[KEY_SINGLETON]:
            log.debug("resetting '%s'", singleton)
            try:
                singleton.reset()
            except Exception as e:
                log.exception(e)

        for obj in self[KEY_OBJECT]:
            log.debug("resetting '%s'", obj)
            try:
                obj.reset()
            except NotImplementedError:
                log.critical("Object '%s@%s' did not implement the reset() method!", obj, obj.__class__)
            except Exception as e:
                log.exception(e)

        log.info("clearing simulate state objects ...")
        self[KEY_OBJECT] = []

