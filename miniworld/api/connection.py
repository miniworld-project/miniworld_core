import graphene
from sqlalchemy.orm.exc import NoResultFound

from miniworld.api import InternalIdentifier, ConnectionTypeInterface, ConnectionInterface
from miniworld.api.node import EmulationNode, NodeConnection
from miniworld.api.interface import Interface
from miniworld.model.domain.connection import Connection as DomainConnection
from miniworld.service.persistence import connections


class Connection(graphene.ObjectType):
    class Meta:
        interfaces = (InternalIdentifier, ConnectionTypeInterface, ConnectionInterface, graphene.relay.Node)

    emulation_node_x = graphene.Field(lambda: EmulationNode)
    emulation_node_y = graphene.Field(lambda: EmulationNode)
    interface_x = graphene.Field(lambda: Interface)
    interface_y = graphene.Field(lambda: Interface)

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
    def serialize_connection(cls, connection: DomainConnection) -> 'Connection':
        return Connection(
            id=connection._id,
            iid=connection._id,
            connected=connection.connected,
            emulation_node_x=EmulationNode.serialize(connection.emulation_node_x),
            emulation_node_y=EmulationNode.serialize(connection.emulation_node_y),
            interface_x=Interface.serialize(connection.interface_x),
            interface_y=Interface.serialize(connection.interface_y),
            kind=connection.connection_type.value,
            distance=connection.distance,
            impairment=connection.impairment if connection.impairment is not None else {},  # TODO: REMOVE after objects come from db!
        )


class NodeConnectionQuery(graphene.ObjectType):
    node_connections = graphene.List(NodeConnection)

    def resolve_node_connections(self, info):
        connection_persistence_service = connections.ConnectionPersistenceService()
        return [NodeConnection.serialize_connection(connection) for connection in connection_persistence_service.all()]


class ConnectionQuery(graphene.ObjectType):
    connections = graphene.List(Connection)

    def resolve_connections(self, info):
        connection_persistence_service = connections.ConnectionPersistenceService()
        return [Connection.serialize_connection(connection) for connection in connection_persistence_service.all()]