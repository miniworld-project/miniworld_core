import enum

import graphene


class DictScalar(graphene.Scalar):
    @staticmethod
    def serialize(x):
        return x


class Status(enum.Enum):
    ok = 1
    error = 2


class InternalIdentifier(graphene.Interface):
    iid = graphene.Int()


class ConnectionTypeInterface(graphene.Interface):
    # TODO: use enum
    kind = graphene.String()


class ConnectionInterface(graphene.Interface):
    impairment = graphene.Field(DictScalar)
    connected = graphene.Boolean()
    distance = graphene.Float()
