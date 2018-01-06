import graphene
from sqlalchemy.orm.exc import NoResultFound

from miniworld.api import InternalIdentifier, ConnectionTypeInterface
from miniworld.model.domain.interface import Interface as InterfaceModel
from miniworld.service.persistence import interfaces


class Interface(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    name = graphene.String()
    nr_host_interface = graphene.Int()
    ipv4 = graphene.String()
    mac = graphene.String()

    @classmethod
    def serialize(cls, interface: InterfaceModel):
        return cls(
            id=interface._id,
            iid=interface._id,
            name=interface.name,
            mac=interface.mac,
            ipv4=interface.ipv4,
            nr_host_interface=interface.nr_host_interface,
        )

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        interface_persistence_service = interfaces.InterfacePersistenceService()

        try:
            interface = interface_persistence_service.get(interface_id=id)
        except NoResultFound:
            return

        return cls.serialize(interface)
