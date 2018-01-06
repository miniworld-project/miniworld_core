import netifaces

from miniworld.errors import NetworkBridgeNotExisting
from miniworld.misc.InterfaceDependentID import InterfaceDependentID
from miniworld.model import StartableObject
from miniworld.singletons import singletons


class AbstractSwitch(StartableObject.ScenarioState, InterfaceDependentID):
    """
    Attributes
    ----------
    id : str
    interface : Interface
    nlog :
    """

    def __init__(self, id, interface):
        """
        Parameters
        ----------
        id : int
        interface : Interface
        colorful : bool
            If the interface shall be colored on the switch.
        """
        StartableObject.ScenarioState.__init__(self)

        self.interface = interface
        # TODO: just for prototyping
        self.id = 10000

        # create extra node logger
        self.nlog = singletons.logger_factory.get_node_logger(id)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.id, self.interface)

    def _start(self, bridge_dev_name=None, switch=False):
        """

        Parameters
        ----------
        bridge_dev_name : str, optional (default is None)
            The name of the device to bridge to.
            If None, don't bridge at all.
        switch : bool, optional (default is False)
            Start as switch. Otherwise as hub.

        Returns
        -------

        Raises
        ------
        NetworkBridgeNotExisting
        """
        if bridge_dev_name and bridge_dev_name not in netifaces.interfaces():
            raise NetworkBridgeNotExisting("""The bridge with name '%s' does not exist!
            Run "sudo ip tuntap add dev %s mode tap"
            """ % (bridge_dev_name, bridge_dev_name))
