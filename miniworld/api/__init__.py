import graphene


class DictScalar(graphene.Scalar):
    @staticmethod
    def serialize(x):
        return x
