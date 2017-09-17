from miniworld.model.network.backends.NetworkBackend import NetworkBackendDummy


def NetworkBackendDynamic():
    class NetworkBackendDynamic(NetworkBackendDummy):

        """
        Base class for :py:class:`.NetworkBackend`s which have real mobile nodes moving on a map.
        Therefore, the movement and connection changes are not known beforehand.
        """
        pass

    return NetworkBackendDynamic
