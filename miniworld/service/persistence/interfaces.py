from miniworld.model.db.base import Interface
from miniworld.model.interface.Interface import Interface as DomainInterface
from miniworld.network.connection import AbstractConnection
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.singletons import singletons


class InterfacePersistenceService:
    def __init__(self):
        self._node_persistence_service = NodePersistenceService()

    @staticmethod
    def to_domain(interface: Interface) -> DomainInterface:
        for node in singletons.simulation_manager.nodes_id_mapping.values():
            for iface in node.network_mixin.interfaces:
                if iface._id == interface.id:
                    return iface
        raise RuntimeError()

        # TODO:
        return DomainInterface(
            _id=interface.id,
            mac=interface.mac,
            ipv4=interface.ipv4,
            ipv6=interface.ipv6,
        )

    # TODO: support kind
    def get(self, interface_id: int, kind: AbstractConnection.ConnectionType = None) -> Interface:
        with singletons.db_session.session_scope() as session:
            return self.to_domain(
                (session.query(Interface)
                 .filter(Interface.id == interface_id)
                 .one())
            )
