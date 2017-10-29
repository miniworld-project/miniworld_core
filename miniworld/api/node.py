import graphene
from graphene import ObjectType

from miniworld import singletons
from miniworld.model.interface.Interface import Interface as InterfaceModel
from miniworld.nodes.EmulationNode import EmulationNode


class Interface(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    nr_host_interface = graphene.Int()
    ipv4 = graphene.String()
    mac = graphene.String()


class Node(ObjectType):
    id = graphene.Int()
    virtualization = graphene.String()
    interfaces = graphene.List(Interface)


class NodeQuery(ObjectType):
    nodes = graphene.List(Node, id=graphene.Int(), others=graphene.List(graphene.Int))

    def resolve_nodes(self, info, id: int = None):
        return [serialize_node(node) for id, node in filter(lambda x: (x[0] == id) if id is not None else True,
                                                            singletons.simulation_manager.nodes_id_mapping.items())
                ]


def serialize_node(node: EmulationNode) -> Node:
    return Node(
        id=node._id,
        virtualization=node.virtualization_layer.__class__.__name__,
        interfaces=[serialize_interface(interface) for interface in
                    node.interfaces]
    )


def serialize_interface(interface: InterfaceModel):
    return Interface(
        id=interface._id,
        name=interface.node_class_name,
        mac=interface.mac,
        ipv4=interface.ipv4,
        nr_host_interface=interface.nr_host_interface,
    )
