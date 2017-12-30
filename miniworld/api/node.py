from collections import defaultdict
from typing import List

import graphene
from sqlalchemy.orm.exc import NoResultFound

from miniworld import singletons
from miniworld.api import InternalIdentifier, ConnectionTypeInterface, ConnectionInterface
from miniworld.api.interface import Interface
from miniworld.model.domain.connection import Connection as DomainConnection
from miniworld.model.domain.node import Node as DomainNode
from miniworld.service.persistence import connections
from miniworld.service.persistence import interfaces, nodes
from miniworld.service.persistence.nodes import NodePersistenceService


class NodeConnection(graphene.ObjectType):
    class Meta:
        interfaces = (InternalIdentifier, ConnectionTypeInterface, ConnectionInterface, graphene.relay.Node)

    emulation_node = graphene.Field(lambda: EmulationNode)
    interface = graphene.Field(lambda: Interface)

    @classmethod
    def get_node(cls, info, id):
        id = int(id)
        connection_persistence_service = connections.ConnectionPersistenceService()

        try:
            connection = connection_persistence_service.get(connection_id=id)
        except NoResultFound:
            return None

        return cls.serialize_connection(connection)

    @classmethod
    def serialize_connection(cls, connection: DomainConnection) -> 'NodeConnection':
        # choose the node and interface which is not the own one
        emulation_node = connection.emulation_node_x if connection.emulation_node_y._id == cls.emulation_node.iid else connection.emulation_node_y
        interface = connection.interface_x if emulation_node == connection.emulation_node_x else connection.interface_y
        return NodeConnection(
            id=connection._id,
            iid=connection._id,
            connected=connection.connected,
            emulation_node=EmulationNode.serialize(emulation_node),
            interface=Interface.serialize(interface),
            kind=connection.connection_type.value,
            distance=connection.distance,
            impairment=connection.impairment if connection.impairment is not None else {},  # TODO: REMOVE after objects come from db!
        )


class Distance(graphene.ObjectType):
    emulation_node = graphene.Field(lambda: EmulationNode)
    distance = graphene.Float()


class EmulationNode(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    class InterfaceConnection(graphene.relay.Connection):
        class Meta:
            node = Interface

    class LinkConnection(graphene.relay.Connection):
        class Meta:
            node = NodeConnection

    class DistanceConnection(graphene.relay.Connection):
        class Meta:
            node = Distance

    class BetweenDistances(graphene.InputObjectType):
        min = graphene.Float(description="distance => min", defaul_value=None)
        max = graphene.Float(description="distance <= max", default_value=None)
        iid = graphene.Int()

    virtualization = graphene.String()

    interfaces = graphene.relay.ConnectionField(
        InterfaceConnection,
        description='The interfaces of the node.'
    )

    links = graphene.relay.ConnectionField(
        LinkConnection,
        connected=graphene.Boolean(),
        kind=graphene.String(),  # TODO: actually enum
    )
    distances = graphene.relay.ConnectionField(
        DistanceConnection,
        between=BetweenDistances()
    )

    @classmethod
    def serialize(cls, node: DomainNode) -> 'EmulationNode':
        return cls(
            id=node._id,
            iid=node._id,
            virtualization='QemuTap',  # TODO: do not hardcode
            interfaces=[Interface.serialize(interface) for interface in node.interfaces],
            links=node.connections,
            kind=node.type.value,
        )

    def resolve_interfaces(self, info) -> List[Interface]:
        # TODO: filter by type!
        interface_persistence_service = interfaces.InterfacePersistenceService()
        return [Interface.serialize(interface_persistence_service.get(interface_id=interface.iid)) for interface in self.interfaces]

    def resolve_links(self, info, connected: bool = None, kind: str = None) -> List[NodeConnection]:
        # TODO: respect connection ids!
        connection_persistence_service = connections.ConnectionPersistenceService()
        return [self._serialize_node_connection(connection) for connection in connection_persistence_service.get_by_node(
            node=DomainNode(_id=self.iid), connection_type=kind, connected=connected,
        )]

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
                    emulation_node=EmulationNode.serialize(singletons.simulation_manager.nodes_id_mapping.get(y)),
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

        return EmulationNode.serialize(node)


class NodeQuery(graphene.ObjectType):
    emulation_nodes = graphene.List(EmulationNode)

    def resolve_emulation_nodes(self, info):
        node_persistence_service = NodePersistenceService()
        return [EmulationNode.serialize(node) for node in node_persistence_service.all()]


class NodeExecuteCommand(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        cmd = graphene.String()
        validate = graphene.Boolean(default_value=None)
        timeout = graphene.Float(default_value=1.0)

    result = graphene.String()

    def mutate(self, info, id: int, cmd: str,
               validate: bool, timeout: float):
        return NodeExecuteCommand(result=singletons.network_backend_bootstrapper.emulation_service.exec_node_cmd(cmd, node_id=id, validation=validate, timeout=timeout))
