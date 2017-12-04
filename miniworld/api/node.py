from collections import defaultdict
from typing import List

import graphene

from miniworld import singletons
from miniworld.api import DictScalar
from miniworld.model.interface.Interface import Interface as InterfaceModel
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.persistence import connections
from miniworld.service.persistence import interfaces, nodes
from miniworld.service.persistence.connections import ConnectionPersistenceService


class InternalIdentifier(graphene.Interface):
    iid = graphene.Int()


class ConnectionTypeInterface(graphene.Interface):
    # TODO: use enum
    kind = graphene.String()


class Interface(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    name = graphene.String()
    nr_host_interface = graphene.Int()
    ipv4 = graphene.String()
    mac = graphene.String()

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        interface_persistence_service = interfaces.InterfacePersistenceService()
        interface = interface_persistence_service.get(interface_id=id)
        if interface is not None:
            return serialize_interface(interface)


class NodeRef(graphene.ObjectType):
    interface = graphene.Field(Interface)
    emulation_node = graphene.Field(lambda: EmulationNode)


class Connection(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    # TODO: add distance
    this = graphene.Field(NodeRef)
    other = graphene.Field(NodeRef)
    impairment = graphene.Field(DictScalar)
    connected = graphene.Boolean()

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        connection_persistence_service = connections.ConnectionPersistenceService()
        connection = connection_persistence_service.get(connection_id=id)
        if connection is not None:
            return serialize_connection(connection)


class Distance(graphene.ObjectType):
    emulation_node = graphene.Field(lambda: EmulationNode)
    distance = graphene.Float()


class InterfaceConnection(graphene.relay.Connection):
    class Meta:
        node = Interface


class LinkConnection(graphene.relay.Connection):
    class Meta:
        node = Connection


class DistanceConnection(graphene.relay.Connection):
    class Meta:
        node = Distance


class BetweenDistances(graphene.InputObjectType):
    min = graphene.Float(description="distance => min", defaul_value=None)
    max = graphene.Float(description="distance <= max", default_value=None)


class EmulationNode(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    iid = graphene.Int()
    virtualization = graphene.String()

    interfaces = graphene.relay.ConnectionField(
        InterfaceConnection,
        description='The interfaces of the node.'
    )

    links = graphene.relay.ConnectionField(
        LinkConnection,
        connected=graphene.Boolean()
    )
    distances = graphene.relay.ConnectionField(
        DistanceConnection,
        between=BetweenDistances()
    )

    def resolve_interfaces(self, info) -> List[Interface]:
        # TODO: filter by type!
        interface_persistence_service = interfaces.InterfacePersistenceService()
        return [serialize_interface(interface_persistence_service.get(interface_id=interface.iid)) for interface in self.interfaces]

    def resolve_links(self, info, iid=None, connected: bool = None) -> List[Connection]:
        # TODO: respect connection ids!
        connection_persistence_service = connections.ConnectionPersistenceService()
        return [serialize_connection(connection_persistence_service.get(connection_id=connection._id)) for connection in self.links]

    def resolve_distances(self, info, between: BetweenDistances = None) -> List[Distance]:

        # TODO: persist distance matrix
        distances = singletons.simulation_manager.movement_director.get_distances_from_nodes()
        if distances:
            distance_objs = defaultdict(list)
            for (x, y), distance in distances.items():

                if between is not None:
                    if isinstance(between.min, float):
                        if not between.min <= distance:
                            continue

                    if isinstance(between.max, float):
                        if not distance <= int(between.max):
                            continue

                distance_objs[x].append(Distance(
                    emulation_node=serialize_node(singletons.simulation_manager.nodes_id_mapping.get(y)),
                    distance=distance
                ))
            return distance_objs[self.iid]

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        node_persistence_service = nodes.NodePersistenceService()
        node = node_persistence_service.get(node_id=id)
        if node is not None:
            return serialize_node(node)


class NodeQuery(graphene.ObjectType):
    emulation_nodes = graphene.List(EmulationNode, iid=graphene.Int(), kind=graphene.String())

    def resolve_emulation_nodes(self, info, iid: int = None, kind=None):
        connection_persistence_service = ConnectionPersistenceService()
        nodes = [serialize_node(node) for id, node in filter(lambda x: (x[0] == iid) if iid is not None else True,
                                                             singletons.simulation_manager.nodes_id_mapping.items())]
        for node in nodes:
            node.links = connection_persistence_service.all(node_x_id=node.id)
        return sorted(nodes, key=lambda node: node.iid)


class NodeExecuteCommand(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        cmd = graphene.String()
        validate = graphene.Boolean(default_value=None)
        timeout = graphene.Float(default_value=1.0)

    result = graphene.String()

    def mutate(self, info, id: int, cmd: str,
               validate: bool, timeout: float):
        return NodeExecuteCommand(result=singletons.simulation_manager.exec_node_cmd(cmd, node_id=id, validation=validate, timeout=timeout))


def serialize_node(node: EmulationNode) -> EmulationNode:
    return EmulationNode(
        id=node._id,
        iid=node._id,
        virtualization=node.virtualization_layer.__class__.__name__,
        interfaces=[serialize_interface(interface) for interface in node.network_mixin.interfaces],
    )


def serialize_interface(interface: InterfaceModel):
    return Interface(
        id=interface._id,
        iid=interface._id,
        name=interface.node_class_name,
        mac=interface.mac,
        ipv4=interface.ipv4,
        nr_host_interface=interface.nr_host_interface,
    )


def serialize_connection(connection: AbstractConnection) -> Connection:
    # TODO: is self always the first?
    return Connection(
        id=connection._id,
        iid=connection._id,
        this=NodeRef(
            interface=serialize_interface(connection.interface_x),
            emulation_node=serialize_node(connection.emulation_node_x),
        ),
        other=NodeRef(
            interface=serialize_interface(connection.interface_y),
            emulation_node=serialize_node(connection.emulation_node_y),
        ),
        impairment=connection.impairment,
        connected=connection.connected,
        kind=connection.connection_type.value,
    )
