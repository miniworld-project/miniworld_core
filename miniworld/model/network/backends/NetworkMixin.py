from miniworld.model import StartableObject
from miniworld.model.network.backends.SwitchMixin import SwitchMixin


class NetworkMixin(StartableObject.StartableSimulationStateObject, SwitchMixin):

    """
    This class decouples the network functionality from the actual node type (e.g. QEMU, Docker, ...).
    Therefore,
    Attributes
    ----------
    interfaces : Interfaces, optional (default is only a mesh interface)
    network_backend_bootstrapper : NetworkBackendBootStrapper
    """

    # TODO: add EmulationNode ref
    def __init__(self, network_backend_boot_strapper):
        StartableObject.StartableSimulationStateObject.__init__(self)

        self.interfaces = None
        self.network_backend_bootstrapper = network_backend_boot_strapper

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.interfaces)
