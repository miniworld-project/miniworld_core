from miniworld.model.db.base import Interface, Node
from miniworld.model.interface.Interface import Interface as DomainInterface
from miniworld.service.persistence.nodes import NodePersistenceService


class InterfacePersistenceService:
    def __init__(self):
        self._node_persistence_service = NodePersistenceService()

    def to_domain(self, node: Node, interface: Interface) -> DomainInterface:
        emulation_node = self._node_persistence_service.to_domain(node)  # type: EmulationNode
        interfaces = emulation_node.network_mixin.interfaces
        for iface in interfaces:
            if interface.id == iface._id:
                return iface
