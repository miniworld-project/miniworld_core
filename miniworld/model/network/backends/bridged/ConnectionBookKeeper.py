import collections
from collections import defaultdict

from miniworld import singletons
from miniworld.model.singletons.Resetable import Resetable


class InterfaceStates(collections.UserDict):
    """
    No reset needed. Reset is done by :py:class:`.ConnectionBookKeeper`
    """

    def __init__(self, *args, **kwargs):
        collections.UserDict.__init__(self, *args, **kwargs)

    def __getitem__(self, item):
        """
        Parameters
        ----------
        item : str
        """
        try:
            # old-style class, no super
            res = collections.UserDict.__getitem__(self, item)
        except KeyError:
            res = self[item] = False
        return res

    def toggle_state(self, dev_name, up):
        if self[dev_name] != up:
            self[dev_name] = up

    def add_device(self, dev_name, up=False):
        self[dev_name] = up


class ConnectionBookKeeper(Resetable):
    """
    Keeps track of connections between hosts and the used tap devices.

    Attributes
    ----------
    connections : dict<(EmulationNode, EmulationNode), bool>
    interface_states : dict<str, bool>
        Remember for each the device whether it is up (True) or down
    """

    def __init__(self):
        object.__init__(self)
        self.connections = defaultdict(lambda: False)
        self.interface_states = InterfaceStates()

    def reset(self):
        self.connections = defaultdict(lambda: False)
        self.interface_states = InterfaceStates()

    # TODO: check for bottleneck! better way?! use core file for tap dev mapping?
    def should_create_new_connection(self, emulation_node_x, emulation_node_y, interface_x, interface_y):
        """
        Check if the two tap devices used for the interfaces are already used.
        Moreover, check if there exists a connection between the two nodes yet.

        A new connection is only created, if both requirements are met.
        An alternative to this method is to use the topology mapping from the core config files.
        Until now, we use only which nodes are connected to each other. But not on which interfaces!

        Checking on demand if a connection shall be created might enable us to make this backend
        dynamic by hotplugging new tap devices into the nodes.
        """

        tap_x = singletons.network_backend.get_tap_name(emulation_node_x.id, interface_x)
        tap_y = singletons.network_backend.get_tap_name(emulation_node_y.id, interface_y)

        # do not connect multiple times
        # NOTE: needed because otherwise the code would connect all interfaces of a node with all interfaces of any other node
        no_connection_between_hosts = not self.connections[(emulation_node_x, emulation_node_y)]
        # ensure both tap devices are not in use
        no_tap_device_used_yet = tap_x not in self.interface_states and tap_y not in self.interface_states

        return no_connection_between_hosts and no_tap_device_used_yet

    def remember_bidirectional_connection(self, emulation_node_x, emulation_node_y, interface_x, interface_y):
        """
        Remember which nodes are connected and which tap devices are already in use.
        This is because a tap device can only be connected to exactly one bridge.

        Parameters
        ----------
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y

        Returns
        -------
        """
        tap_x = singletons.network_backend.get_tap_name(emulation_node_x.id, interface_x)
        tap_y = singletons.network_backend.get_tap_name(emulation_node_y.id, interface_y)

        self.interface_states.add_device(tap_x)
        self.interface_states.add_device(tap_y)
        self.connections[(emulation_node_x, emulation_node_y)] = True

    def remember_unidirectional_connection(self, tap_dev):

        self.interface_states.add_device(tap_dev)
