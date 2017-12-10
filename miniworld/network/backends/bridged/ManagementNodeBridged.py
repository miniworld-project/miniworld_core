from miniworld.model.domain.node import Node
from miniworld.singletons import singletons
from miniworld.model import ResetableInterface
from miniworld.nodes.virtual import ManagementNode


class ManagementNodeBridged(ManagementNode.ManagementNode, ResetableInterface.ResetableInterface):
    """
    A `VirtualNode` whose hub/switch is colored.
    The link quality of its connections are not influenced by the distance matrix.
    No link quality adjustment is done. This is intended for management stuff.
    """

    def __init__(self, node: Node):
        ManagementNode.ManagementNode.__init__(self, node=node)

    def _start(self, switch=True, bridge_dev_name=None):
        # TODO: DOC, NetlinkError: (34, 'Numerical result out of range')

        self.name = singletons.config.get_bridge_tap_name()
        ManagementNode.ManagementNode._start(self, switch=switch, bridge_dev_name=bridge_dev_name)
        self.switch.id = singletons.config.get_bridge_tap_name()

    def reset(self):
        """ Shutdown the bridge """
        self.switch.reset()
