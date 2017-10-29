import graphene
from collections import defaultdict

from miniworld.api import DictScalar
from miniworld.api.node import Node, Interface, serialize_node, serialize_interface
from miniworld.singletons import singletons


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
        return list(resolve_impairments(id=id, active=active))


def resolve_impairments(id: int = None, active: bool = None):
    # TODO: ticket to support generators in graphene
    #  singletons.network_manager.connection_store.get_connections() returns duplicate values
    links = defaultdict(set)

    def add_impairment(emu_nodes, interfaces, connection_details, connected):
        links[(emu_nodes[0], interfaces[0])].add(
            Connection(
                node=serialize_node(emu_nodes[1]),
                interface=serialize_interface(interface=interfaces[1]),
                impairment=connection_details.link_quality,
                connected=connected,
            ),
        )

    for node in filter(lambda node: (node._id == id) if id is not None else True, singletons.simulation_manager.nodes_id_mapping.values()):
        if active is None or active is True:
            for emu_nodes, interfaces, connection_details in singletons.network_manager.connection_store.get_connections(
                    node, active=True):
                add_impairment(emu_nodes, interfaces, connection_details, True)
        if active is None or active is False:
            for emu_nodes, interfaces, connection_details in singletons.network_manager.connection_store.get_connections(
                    node, active=False):
                add_impairment(emu_nodes, interfaces, connection_details, False)
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
