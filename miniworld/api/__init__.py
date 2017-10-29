import enum

import graphene


class DictScalar(graphene.Scalar):
    @staticmethod
    def serialize(x):
        return x


class Status(enum.Enum):
    ok = 1
    error = 2
