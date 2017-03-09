import UserList

from miniworld.model.singletons import Resetable


class SimulationErrors(UserList.UserList, Resetable.Resetable):
    '''
    Attributes
    ----------
    data : list<Exception, None, traceback>
    '''

    def reset(self):
        self.data = []

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.data)