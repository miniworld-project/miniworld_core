from miniworld.errors import Base
from miniworld.model.singletons.Singletons import singletons

class AlreadyStartedError(Base):
    pass

class AlreadyPerformedShutdownError(Base):
    pass

# TODO: DOC
class StartableObject(object):

    def __init__(self):
        self.started = False
        self.shutdown_completed = False

    def start(self, *args, **kwargs):
        if self.started:
            raise AlreadyStartedError(self.get_already_called_once_msg(self._start))
        self._start(*args, **kwargs)
        self.shutdown_completed = False
        self.started = True

    def _start(self, *args, **kwargs):
        raise NotImplementedError

    def shutdown(self, *args, **kwargs):
        if self.shutdown_completed:
            raise AlreadyPerformedShutdownError(self.get_already_called_once_msg(self._shutdown))
        self._shutdown(*args, **kwargs)

        self.shutdown_completed = True
        self.started = False

    def get_already_called_once_msg(self, fun):
        return "The method '%s' of class '%s' has already been called once!" % (
            fun.__name__, self.__class__.__name__)

    def _shutdown(self, *args, **kwargs):
        raise NotImplementedError

# TODO: #54,#55: DOC

class StartableSimulationStateObject(StartableObject):

    def __init__(self):
        super(StartableSimulationStateObject, self).__init__()
        singletons.simulation_state_gc.add_tmp_object_with_simulation_scenario_state(self)

    def reset(self):
        raise NotImplementedError
