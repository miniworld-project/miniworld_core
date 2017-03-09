from UserDict import UserDict


class TupleUserDict(UserDict, object):

    #########################################
    ### Implement these in a subclass
    #########################################

    # TODO: implement same behaviour via magic methods ...
    @staticmethod
    def _get_key(*args, **kwargs):
        raise NotImplementedError

    #########################################
    ### Magic Methods
    #########################################

    def __getitem__(self, item):
        '''
        Parameters
        ----------
        item : (Interface, Interface)
        '''
        item = self._get_key(*item)

        # old-style class, no super
        res = UserDict.__getitem__(self, item)

        return res

    def __setitem__(self, key, item):
        '''
        Parameters
        ----------
        key: (Interface, Interface)
        item : object
        '''
        key = self._get_key(*key)
        # old-style class, no super
        return UserDict.__setitem__(self, key, item)

    def __delitem__(self, key):
        '''
        Parameters
        ----------
        item : (Interface, Interface)
        '''
        key = self._get_key(*key)
        # old-style class, no super
        return UserDict.__delitem__(self, key)

    # NOTE: important for get() to work properly!
    def __contains__(self, key):
        '''
        Parameters
        ----------
        key : (Interface, Interface)
        '''
        key = self._get_key(*key)
        # old-style class, no super
        return UserDict.__contains__(self, key)