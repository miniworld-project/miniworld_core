import graphene
from miniworld.singletons import singletons
from miniworld.api import DictScalar


class ImpairmentState(graphene.ObjectType):
    connected = graphene.Boolean()
    settings = graphene.Field(DictScalar)


class ImpairmentModel(graphene.ObjectType):
    max_connected = graphene.Int()
    initial = graphene.Field(ImpairmentState)
    requested = graphene.Field(ImpairmentState)


class ImpairmentQuery(graphene.ObjectType):
    impairment = graphene.Field(ImpairmentModel, distance=graphene.Int())

    def resolve_impairment(self, info, distance: float = None):
        impairment_obj = singletons.simulation_manager.impairment
        if impairment_obj is None:
            return ImpairmentModel(max_connected=None)

        if distance is not None:
            connected, impairment = impairment_obj.distance_2_link_quality(distance)
            requested = ImpairmentState(
                connected=connected, settings=impairment)
        else:
            requested = None
        connected_initial, impairment_initial = impairment_obj.get_initial_link_quality()
        return ImpairmentModel(
            requested=requested,
            initial=ImpairmentState(
                connected=connected_initial, settings=impairment_initial),
            max_connected=impairment_obj.max_connected_distance,
        )
