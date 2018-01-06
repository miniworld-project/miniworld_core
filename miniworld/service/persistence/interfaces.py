from miniworld.model.db.base import Interface
from miniworld.model.domain.interface import Interface as DomainInterface
from miniworld.network.connection import AbstractConnection
from miniworld.singletons import singletons


class InterfacePersistenceService:

    @staticmethod
    def to_domain(interface: Interface) -> DomainInterface:
        return DomainInterface(
            _id=interface.id,
            name=interface.name,
            nr_host_interface=interface.nr_host_interface,
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

    # TODO: generic update ?
    def update_ipv4(self, interface: DomainInterface, ipv4: str):
        with singletons.db_session.session_scope() as session:
            (session.query(Interface)
             .filter(Interface.id == interface._id)
             .update({Interface.ipv4: ipv4})
             )
            interface.ipv4 = ipv4

    def update_mac(self, interface: DomainInterface, mac: str):
        with singletons.db_session.session_scope() as session:
            (session.query(Interface)
             .filter(Interface.id == interface._id)
             .update({Interface.ipv4: mac})
             )
            interface.mac = mac
