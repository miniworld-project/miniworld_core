import graphene
from graphene import ObjectType

from miniworld import singletons


class Interfaces(ObjectType):
    pass


class Interface(ObjectType):
    node_class = graphene.Int()
    node_class_name = graphene.String()
    nr_host_interface = graphene.Int()
    # ip = graphene.String()
    mac = graphene.String()


class Node(ObjectType):
    id = graphene.Int()
    virtualization = graphene.String()
    interfaces = graphene.List(Interface)


class NodeQuery(ObjectType):
    nodes = graphene.List(Node, id=graphene.Int())

    def resolve_nodes(self, info, **kwargs):
        node_id = kwargs.get('id')
        return [Node(
            id=node.id,
            virtualization=node.virtualization_layer.__class__.__name__,
            interfaces=[Interface(
                mac=node.interfaces[0].get_mac(node.id),
                node_class=node.interfaces[0].node_class,
                node_class_name=node.interfaces[0].node_class_name,
                nr_host_interface=node.interfaces[0].nr_host_interface,
            )]
        ) for id, node in filter(
            lambda x: x[0] == node_id if node_id is not None else True,
            singletons.simulation_manager.nodes_id_mapping.items())
        ]
