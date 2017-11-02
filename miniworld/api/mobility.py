"""
singletons.simulation_manager.movement_director.get_coordinates_for_nodes()
"""
from typing import Iterator

import graphene

from collections import defaultdict
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
        return sorted(serialize_distances(node_id=id, between=between),
                      key=lambda distance: distance.node.id
                      )


def serialize_linked_node(node, distance_details):
    partial = serialize_node(node)
    partial.links = distance_details
    return partial


def serialize_distances(node_id: int = None, between: BetweenDistances = None) -> Iterator[Distance]:
    distances = singletons.simulation_manager.movement_director.get_distances_from_nodes()
    distance_details = defaultdict(list)
    for (x, y), distance in distances.items():

        # filters
        if node_id is not None and x != node_id:
            continue
        if between is not None:
            if not between.min <= distance <= between.max:
                continue

        distance_details[x].append(DistanceDetails(
            node=serialize_node(singletons.simulation_manager.nodes_id_mapping[y]),
            distance=distance
        ))

    for node_id, distance_details in distance_details.items():
        node = singletons.simulation_manager.nodes_id_mapping[node_id]
        res = Distance(
            node=serialize_linked_node(node, distance_details),
        )
        yield res
