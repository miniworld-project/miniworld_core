from collections import defaultdict
from typing import List

import graphene
from sqlalchemy.orm.exc import NoResultFound

from miniworld import singletons
from miniworld.api import InternalIdentifier, ConnectionTypeInterface
from miniworld.api.interface import Interface
from miniworld.model.domain.node import Node as DomainNode
from miniworld.service.persistence import interfaces, nodes
from miniworld.service.persistence.nodes import NodePersistenceService


class Distance(graphene.ObjectType):
    emulation_node = graphene.Field(lambda: EmulationNode)
    distance = graphene.Float()


class EmulationNode(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node, InternalIdentifier, ConnectionTypeInterface)

    class InterfaceConnection(graphene.relay.Connection):
        class Meta:
            node = Interface

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
            kind=node.type.value,
        )

    def resolve_interfaces(self, info) -> List[Interface]:
        # TODO: filter by type!
        interface_persistence_service = interfaces.InterfacePersistenceService()
        return [Interface.serialize(interface_persistence_service.get(interface_id=interface.iid)) for interface in self.interfaces]

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
