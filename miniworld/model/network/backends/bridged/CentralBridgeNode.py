from miniworld.model.singletons.Singletons import singletons
from miniworld.model.emulation.nodes.virtual import CentralNode


class CentralBridgeNode(CentralNode.CentralNode):
    """
    Attributes
    ----------
    bridge : Bridge
    """

    def __init__(self, network_backend_bootstrapper, id=id):
        id = 'br_cn_%s' % id
        CentralNode.CentralNode.__init__(self, network_backend_bootstrapper, id=id)

    def _start(self, switch=True, bridge_dev_name=None):
        super(CentralBridgeNode, self)._start(switch=switch, bridge_dev_name=bridge_dev_name)
        # self.switch.start(switch=switch)

    def get_bridge_name(self, id, interface):
        return singletons.network_backend.get_br_name(id, interface)
