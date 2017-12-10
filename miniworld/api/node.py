from collections import defaultdict
from typing import List

import graphene
from sqlalchemy.orm.exc import NoResultFound

from miniworld import singletons
from miniworld.api import DictScalar
from miniworld.nodes.EmulationNode import EmulationNode as DomainEmulationNode
from miniworld.model.domain.connection import Connection as DomainConnection
from miniworld.model.domain.interface import Interface as InterfaceModel
from miniworld.service.persistence import connections
from miniworld.service.persistence import interfaces, nodes
from miniworld.service.persistence.nodes import NodePersistenceService


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

        try:
            interface = interface_persistence_service.get(interface_id=id)
        except NoResultFound:
            return

        return serialize_interface(interface)


class NodeRef(graphene.ObjectType):
    interface = graphene.Field(lambda: Interface)
    emulation_node = graphene.Field(lambda: EmulationNode)


class Connection(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    emulation_node_x = graphene.Field(lambda: EmulationNode)
    emulation_node_y = graphene.Field(lambda: EmulationNode)
    interface_x = graphene.Field(lambda: Interface)
    interface_y = graphene.Field(lambda: Interface)
    impairment = graphene.Field(DictScalar)
    connected = graphene.Boolean()
    distance = graphene.Float()

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        connection_persistence_service = connections.ConnectionPersistenceService()

        try:
            connection = connection_persistence_service.get(connection_id=id)
        except NoResultFound:
            return None

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

    def resolve_links(self, info, connected: bool = None) -> List[Connection]:
        # TODO: respect connection ids!
        connection_persistence_service = connections.ConnectionPersistenceService()
        return [serialize_connection(connection_persistence_service.get(connection_id=connection._id)) for connection in self.links]

    def resolve_distances(self, info, between: BetweenDistances = None) -> List[Distance]:
        # TODO: use persistence service! current implementation returns the next distance matrix!

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

        try:
            node = node_persistence_service.get(node_id=id)
        except NoResultFound:
            return

        return serialize_node(node)


class NodeQuery(graphene.ObjectType):
    emulation_nodes = graphene.List(EmulationNode)

    def resolve_emulation_nodes(self, info):
        node_persistence_service = NodePersistenceService()
        return [serialize_node(node) for node in node_persistence_service.all()]


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


def serialize_node(node: DomainEmulationNode) -> EmulationNode:
    return EmulationNode(
        id=node._node._id,
        iid=node._node._id,
        virtualization='QemuTap',  # TODO: do not hardcode
        interfaces=[serialize_interface(interface) for interface in node._node.interfaces],
        links=node._node.connections,
        kind=node._node.type.value,
    )


def serialize_interface(interface: InterfaceModel):
    return Interface(
        id=interface._id,
        iid=interface._id,
        name=interface.name,
        mac=interface.mac,
        ipv4=interface.ipv4,
        nr_host_interface=interface.nr_host_interface,
    )


def serialize_connection(connection: DomainConnection) -> Connection:
    return Connection(
        id=connection._id,
        iid=connection._id,
        connected=connection.connected,
        emulation_node_x=serialize_node(connection.emulation_node_x),
        emulation_node_y=serialize_node(connection.emulation_node_y),
        interface_x=serialize_interface(connection.interface_x),
        interface_y=serialize_interface(connection.interface_y),
        kind=connection.connection_type.value,
        distance=connection.distance,
        impairment=connection.impairment if connection.impairment is not None else {},  # TODO: REMOVE after objects come from db!
    )
