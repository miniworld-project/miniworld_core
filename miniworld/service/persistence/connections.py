from typing import List, Dict

from miniworld.model.db.base import Connection
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.service.persistence.interfaces import InterfacePersistenceService
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.singletons import singletons


class ConnectionPersistenceService:
    def __init__(self):
        self._node_persistence_service = NodePersistenceService()
        self._interface_persistence_service = InterfacePersistenceService()

    def add(self, connection: Connection):
        is_domain = False
        db_connection = connection
        if isinstance(connection, AbstractConnection):
            is_domain = True
            db_connection = Connection.from_domain(connection)
        with singletons.db_session.session_scope() as session:
            db_connection.step_added = singletons.simulation_manager.current_step
            # very dirty hack to let sqlite start with autoincrement = 0
            conn = session.query(Connection).get(0)
            if not conn:
                db_connection.id = 0
            session.add(db_connection)
        if is_domain:
            connection._id = db_connection.id

    def get(self, **kwargs) -> AbstractConnection:
        with singletons.db_session.session_scope() as session:
            query = session.query(Connection)
            query = self._add_filters(query, **kwargs)
            connection = query.one()

            return self.to_domain(connection)

    def all(self, **kwargs) -> List[AbstractConnection]:
        with singletons.db_session.session_scope() as session:
            query = session.query(Connection)
            query = self._add_filters(query, **kwargs)
            connections = query.all()
            return [self.to_domain(connection) for connection in connections]

    def get_new(self, **kwargs) -> List[AbstractConnection]:
        """ New connections are those which have been added in the current step """
        with singletons.db_session.session_scope() as session:
            query = session.query(Connection)
            query = self._add_filters(query, step=singletons.simulation_manager.current_step, **kwargs)
            connections = query.all()
            return [self.to_domain(connection) for connection in connections]

    def exists(self, **kwargs) -> bool:
        with singletons.db_session.session_scope() as session:
            query = session.query(Connection)
            query = self._add_filters(query, **kwargs)
            return query.first() is not None

    def update_impairment(self, connection_id: int, impairment: Dict):
        with singletons.db_session.session_scope() as session:
            (session.query(Connection)
             .filter(Connection.id == connection_id)
             .update({Connection.impairment: impairment})
             )

    def update_state(self, connection_id: int, connected: bool):
        with singletons.db_session.session_scope() as session:
            (session.query(Connection)
             .filter(Connection.id == connection_id)
             .update({Connection.connected: connected})
             )

    def delete(self):
        with singletons.db_session.session_scope() as session:
            session.query(Connection).delete()

    @staticmethod
    def to_domain(connection: Connection) -> AbstractConnection:
        return singletons.network_manager.connections[connection.id]

    def _add_filters(self, query, connection_id: int = None, connected: bool = None, connection_type: AbstractConnection.ConnectionType = None, step: int = None, interface_x_id: int = None, interface_y_id: int = None, node_x_id: int = None, node_y_id: int = None):
        if connection_id is not None:
            query = query.filter(Connection.id == connection_id)
        if connected is not None:
            query = query.filter(Connection.connected == connected)
        if connection_type is not None:
            query = query.filter(Connection.type == connection_type)
        if step is not None:
            query = query.filter(Connection.step_added == step)
        if interface_x_id is not None:
            query = query.filter(Connection.interface_x_id == interface_x_id)
        if interface_y_id is not None:
            query = query.filter(Connection.interface_y_id == interface_y_id)
        if node_x_id is not None:
            query = query.filter(Connection.node_x_id == node_x_id)
        if node_y_id is not None:
            query = query.filter(Connection.node_y_id == node_y_id)

        query = query.order_by(Connection.node_x_id)
        query = query.order_by(Connection.node_y_id)
        query = query.order_by(Connection.interface_x_id)
        query = query.order_by(Connection.interface_y_id)

        return query
