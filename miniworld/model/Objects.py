from collections import UserList


class Objects(UserList):

    def __hash__(self):
        return hash(tuple(self))

    # TODO: DOC
    def filter_type(self, _type=None, fun=None):

        if type is None and fun is None:
            raise ValueError("Either `_type` or `fun` must be supplied!")

        if fun is None and _type is not None:
            fun = lambda _if: type(_if) == _type

        return self.__class__(list(filter(fun, self)))

    def sorted(self):
        return self.__class__(sorted(self))