from miniworld.model.domain.node import Node
from miniworld.nodes.virtual import CentralNode
from miniworld.singletons import singletons


class CentralBridgeNode(CentralNode.CentralNode):
    """
    Attributes
    ----------
    bridge : Bridge
    """

    def start(self, node: Node):
        super(CentralBridgeNode, self).start(node=node)

    def get_bridge_name(self, id, interface):
        return singletons.network_backend.get_br_name(id, interface)
