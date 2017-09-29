from miniworld import config
from miniworld.model.emulation.nodes.virtual import ManagementNode
from miniworld.model.singletons import Resetable


class ManagementNodeBridged(ManagementNode.ManagementNode, Resetable.Resetable):
    """
    A `VirtualNode` whose hub/switch is colored.
    The link quality of its connections are not influenced by the distance matrix.
    No link quality adjustment is done. This is intended for management stuff.
    """

    def __init__(self, network_backend_bootstrapper):
        ManagementNode.ManagementNode.__init__(self, network_backend_bootstrapper)

    # TODO: intergrate with vdeswitch backend, bridge by default up? autpcreation? tap vs bridge
    def _start(self, switch=True, bridge_dev_name=None):
        # TODO: DOC, NetlinkError: (34, 'Numerical result out of range')

        self.name = config.get_bridge_tap_name()
        self.id
        ManagementNode.ManagementNode._start(self, switch=switch, bridge_dev_name=bridge_dev_name)
        self.switch.id = config.get_bridge_tap_name()

    def reset(self):
        """ Shutdown the bridge """
        self.switch.reset()
