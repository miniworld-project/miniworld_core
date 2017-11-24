import graphene
from collections import defaultdict

from typing import List

from miniworld.api import DictScalar
from miniworld.api.node import Node, Interface, serialize_node, serialize_interface
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.persistence import connections as conns


# TODO: implement __eq__ and __hash__ and use domain model id
class Connection(graphene.ObjectType):
    node = graphene.Field(lambda: Node)
    interface = graphene.Field(lambda: Interface)
    impairment = graphene.Field(DictScalar)
    connected = graphene.Boolean()


class ImpairmentNode(Node):
    id = graphene.Int()
    virtualization = graphene.String()
    interface = graphene.Field(lambda: Interface)
    links = graphene.List(Connection)


class Impairment(graphene.ObjectType):
    node = graphene.Field(ImpairmentNode)


class ImpairmentsQuery(graphene.ObjectType):
    impairments = graphene.List(Impairment, id=graphene.Int(), active=graphene.Boolean(description='Only include (in)active connections'))

    def resolve_impairments(self, info, id: int = None, active: bool = None):
        connection_persistence_service = conns.ConnectionPersistenceService()
        connections = connection_persistence_service.all(
            id=id,
            active=active
        )
        return list(serialize_impairments(connections))


def serialize_impairments(connections: List[AbstractConnection]):
    # TODO: ticket to support generators in graphene
    #  singletons.network_manager.connection_store.get_connections() returns duplicate values
    links = defaultdict(set)

    def add_impairment(connection: AbstractConnection):
        links[(connection.emulation_node_x, connection.interface_x)].add(
            Connection(
                node=serialize_node(connection.emulation_node_y),
                interface=serialize_interface(interface=connection.interface_y),
                impairment=connection.impairment,
                connected=connection.connected,
            ),
        )

    for connection in connections:
        add_impairment(connection)
    for (emu_node, interface), links in links.items():
        yield Impairment(
            node=serialize_impairment_node(emu_node, interface, links)

        )


def serialize_impairment_node(node, interface, links):
    return ImpairmentNode(
        id=node._id,
        virtualization=node.virtualization_layer.__class__.__name__,
        interface=serialize_interface(interface),
        links=links,
    )
