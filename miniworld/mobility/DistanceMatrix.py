from collections import UserDict, OrderedDict
from collections import defaultdict

from ordered_set import OrderedSet


def transform_distance_matrix(distance_matrix):
    """

    Parameters
    ----------
    distance_matrix

    Returns
    -------
    dict<int, list<(int, int)>
    """
    res = defaultdict(list)
    for (x, y), distance in distance_matrix.items():
        res[x].append((y, distance))
    return res


def detransform_distance_matrix(distance_matrix):
    """

    Parameters
    ----------
    distance_matrix

    Returns
    -------
    DistanceMatrix
    """
    res = {}
    for x, entries in distance_matrix.items():
        for (y, distance) in entries:
            res[(int(x), y)] = distance
    return factory()(res)


def factory():
    return DistanceMatrixDict


class DistanceMatrix:
    def __init__(self, data=None):
        """
        Each subclass has to provide a constructor which
        can be used to create a new instance of a :py:class:`.DistanceMatrix`
        by supplying the data as dict.

        Parameters
        ----------
        data : dict<(int, int), int>
        """
        if data is None:
            data = {}
        self.data = data

    def filter_empty(self):
        return factory()(list(filter(lambda x: x[1] >= 0, self.data.items())))

    @staticmethod
    def factory():
        return DistanceMatrixDict

    def get_key(self, x, y):
        raise NotImplementedError

    def set_distance(self, x, y, distance):
        raise NotImplementedError

    def set_unlimited_distance(self, x, y):
        """
        If two nodes shall not be connected at all, we set no distance at all.
        Therefore we can save bytes in the matrix.

        Parameters
        ----------
        x
        y
        distance

        Returns
        -------

        """
        raise NotImplementedError

    def get_distance(self, x, y):
        raise NotImplementedError


class DistanceMatrixDict(UserDict, DistanceMatrix):
    UNLIMITED_DISTANCE = -1

    def __init__(self, data=None):
        DistanceMatrix.__init__(self, data=data)

    def get_key(self, x, y):
        return x, y

    def set_distance(self, x, y, distance):
        self.data[self.get_key(x, y)] = distance

    def set_unlimited_distance(self, x, y):
        self.set_distance(x, y, self.UNLIMITED_DISTANCE)

    def get_distance(self, x, y):
        return self.data[self.get_key((x, y))]

    def diff(self, other: DistanceMatrix) -> DistanceMatrix:
        # new dict with entries present in the first set, but not in the second
        distance_matrix_diff = OrderedDict(list(
            OrderedSet(other.data.items()) - OrderedSet(self.data.items())))
        return DistanceMatrix.factory()(distance_matrix_diff)

    def update(self, other: DistanceMatrix):
        self.data.update(other.data)


if __name__ == '__main__':
    x = {(1, 2): 1, (2, 1): 3}
    print(x)
    x = transform_distance_matrix(x)
    print(x)
    x = detransform_distance_matrix(x)
    print(x)

    x = DistanceMatrix()
    x.set_distance(1, 2, 1)
    x.set_distance(2, 1, 3)
