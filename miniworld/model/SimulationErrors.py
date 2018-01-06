import collections

from miniworld.model import ResetableInterface


class SimulationErrors(collections.UserList, ResetableInterface.ResetableInterface):
    """
    Attributes
    ----------
    data : list<Exception, None, traceback>
    """

    def reset(self):
        self.data = []

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.data)
