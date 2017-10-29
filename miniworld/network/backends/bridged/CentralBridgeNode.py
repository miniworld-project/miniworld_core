from miniworld.nodes.virtual import CentralNode
from miniworld.singletons import singletons


class CentralBridgeNode(CentralNode.CentralNode):
    """
    Attributes
    ----------
    bridge : Bridge
    """

    def _start(self, switch=True, bridge_dev_name=None):
        super(CentralBridgeNode, self)._start(switch=switch, bridge_dev_name=bridge_dev_name)

    def get_bridge_name(self, id, interface):
        return singletons.network_backend.get_br_name(id, interface)
