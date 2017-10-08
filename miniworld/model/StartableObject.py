from miniworld.errors import Base
from miniworld.singletons import singletons


class AlreadyStartedError(Base):
    pass


class AlreadyPerformedShutdownError(Base):
    pass


class StartableObject:
    """ Provides a start and shutdown method and ensures both are called exactly once. """

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


class ScenarioState(StartableObject):
    """ Object whose state can be cleared with the `shutdown` method at the end of a scenario. """

    def __init__(self):
        super().__init__()
        singletons.simulation_state_gc.add_object(self)

    def reset(self):
        self.shutdown()
