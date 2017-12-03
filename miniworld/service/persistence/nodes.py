from sqlalchemy import exists
from typing import List

from sqlalchemy.orm import joinedload

from miniworld.model.db.base import Node
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.singletons import singletons


class NodePersistenceService:
    def add(self, node: Node) -> Node:
        is_domain = False
        db_node = node
        if isinstance(node, EmulationNode):
            db_node = Node.from_domain(node)
            is_domain = True
        with singletons.db_session.session_scope() as session:
            # very dirty hack to let sqlite start with autoincrement = 0
            if db_node.id is None and not session.query(Node).get(0):
                db_node.id = 0
            # for interface in node.interfaces:
            #     session.add(interface)
            session.add(db_node)
            session.commit()

        if is_domain:
            node._id = db_node.id
            singletons.simulation_manager.nodes_id_mapping[node._id] = node

        return node

    def get(self, **kwargs) -> EmulationNode:
        with singletons.db_session.session_scope() as session:
            query = session.query(Node)
            query = self._add_filters(query, **kwargs)
            node = query.options(joinedload('connections')).one()
            node = self.to_domain(node)
            return node

    def all(self, **kwargs) -> List[EmulationNode]:
        with singletons.db_session.session_scope() as session:
            query = session.query(Node)
            query = self._add_filters(query, **kwargs)
            nodes = query.all()

            return [self.to_domain(n) for n in nodes]

    def exists(self, node_id) -> bool:
        with singletons.db_session.session_scope() as session:
            return session.query(exists().where(Node.id == node_id)).scalar()

    def to_domain(self, node: Node) -> EmulationNode:
        from miniworld.service.persistence.connections import ConnectionPersistenceService
        emulation_node = singletons.simulation_manager.nodes_id_mapping[node.id]
        emulation_node.connections = [ConnectionPersistenceService.to_domain(connection) for connection in node.connections]
        return emulation_node

    @staticmethod
    def _add_filters(query, node_id: int = None, connection_type: AbstractConnection.ConnectionType = None):
        if node_id is not None:
            query = query.filter(Node.id == node_id)
        if connection_type is not None:
            query = query.filter(Node.type == connection_type)

        return query
