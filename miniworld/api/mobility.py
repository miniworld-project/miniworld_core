"""
singletons.simulation_manager.movement_director.get_coordinates_for_nodes()
"""
from typing import Iterator

import graphene

from miniworld.api.node import Node, serialize_node
from miniworld.singletons import singletons


class DistanceDetails(graphene.ObjectType):
    node = graphene.Field(Node)
    distance = graphene.Float()


class LinkedNode(Node):
    links = graphene.List(DistanceDetails)


class Distance(graphene.ObjectType):
    node = graphene.Field(LinkedNode)


class BetweenDistances(graphene.InputObjectType):
    min = graphene.Int(description="distance => min")
    max = graphene.Int(description="distance <= max")


class DistancesQuery(graphene.ObjectType):
    distances = graphene.List(Distance, id=graphene.Int(), between=BetweenDistances())

    def resolve_distances(self, info, id: int = None, between: BetweenDistances = None):
        return list(serialize_distances(node_id=id, between=between))


def serialize_linked_node(node, distance_details):
    partial = serialize_node(node)
    partial.links = distance_details
    return partial


def serialize_distances(node_id: int = None, between: BetweenDistances = None) -> Iterator[Distance]:
    distances = singletons.simulation_manager.movement_director.get_distances_from_nodes()
    last_x = None
    distance_details = []
    for (x, y), distance in distances.items():

        # filters
        if node_id is not None and x != node_id:
            continue
        if between is not None:
            if not between.min <= distance <= between.max:
                continue

        if last_x is not None and last_x != x:
            node = singletons.simulation_manager.nodes_id_mapping[last_x]
            res = Distance(
                node=serialize_linked_node(node, distance_details),
            )
            distance_details = []
            yield res

        distance_details.append(DistanceDetails(
            node=singletons.simulation_manager.nodes_id_mapping[y],
            distance=distance
        ))

        last_x = x

    if distance_details:
        node = singletons.simulation_manager.nodes_id_mapping[last_x]
        yield Distance(
            node=serialize_linked_node(node, distance_details),
        )
