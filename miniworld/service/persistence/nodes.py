from multiprocessing import Lock
from typing import List

from sqlalchemy import exists
from sqlalchemy.orm import joinedload

from miniworld.model.db.base import Node, Interface
from miniworld.model.domain.interface import Interface as DomainInterface
from miniworld.model.domain.node import Node as DomainNode
from miniworld.network.connection import AbstractConnection
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.singletons import singletons

lock = Lock()


class NodePersistenceService:
    def add(self, node: Node) -> Node:
        # there is an error with sqlite3 and concurrent inserts, the multiprocessing lock is ok for now
        # in the distributed mode (with postgres?) we need to check again for issues
        with lock:
            is_domain = False
            db_node = node
            if isinstance(node, DomainNode):
                db_node = Node.from_domain(node)
                is_domain = True

            with singletons.db_session.session_scope() as session:
                session.query(Node).with_for_update().all()
                session.query(Interface).with_for_update().all()

                first_node_entry = session.query(Node).get(0) is None
                first_interface_entry = session.query(Interface).get(0) is None

                # very dirty hack to let sqlite start with autoincrement = 0
                if db_node.id is None and first_node_entry:
                    db_node.id = 0
                session.add(db_node)

                for db_interface in db_node.interfaces:
                    # very dirty hack to let sqlite start with autoincrement = 0
                    if db_interface.id is None and first_interface_entry:
                        db_interface.id = 0
                        first_interface_entry = False
                        db_interface.node = db_node
                    session.add(db_interface)
                session.flush()

                for db_interface, interface in zip(db_node.interfaces, node.interfaces):
                    assert db_interface.id is not None
                    if is_domain:
                        assert isinstance(interface, DomainInterface)
                        interface._id = db_interface.id

                if is_domain:
                    assert isinstance(node, DomainNode)
                    node._id = db_node.id
                    assert node._id is not None

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

    # def to_domain(self, node: Node) -> DomainNode:
    #     interfaces = [InterfacePersistenceService.to_domain(interface for interface in node.interfaces)]
    #     return DomainNode(
    #         _id=node.id,
    #         type=node.type,
    #         connections=node.connections,
    #         interfaces=interfaces
    #
    #    )

    def to_domain(self, node: Node, include_connections=True) -> EmulationNode:
        from miniworld.service.persistence.connections import ConnectionPersistenceService
        emulation_node = singletons.simulation_manager.nodes_id_mapping[node.id]
        if include_connections:
            emulation_node._node.connections = [ConnectionPersistenceService.to_domain(connection) for connection in node.connections]
        return emulation_node

    @staticmethod
    def _add_filters(query, node_id: int = None, connection_type: AbstractConnection.ConnectionType = None):
        if node_id is not None:
            query = query.filter(Node.id == node_id)
        if connection_type is not None:
            query = query.filter(Node.type == connection_type)

        return query
