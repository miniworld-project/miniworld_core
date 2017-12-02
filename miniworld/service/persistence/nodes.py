from sqlalchemy import exists
from typing import List

from miniworld.model.db.base import Node
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.singletons import singletons


class NodePersistenceService:
    def add(self, node: Node) -> Node:
        with singletons.db_session.session_scope() as session:
            # very dirty hack to let sqlite start with autoincrement = 0
            if node.id is None and not session.query(Node).get(0):
                node.id = 0
            # for interface in node.interfaces:
            #     session.add(interface)
            session.add(node)
            session.commit()

        return node

    def get(self, node_id: int) -> Node:
        with singletons.db_session.session_scope() as session:
            self.to_domain(session.query(Node).get(node_id))

    def all(self) -> List[EmulationNode]:
        with singletons.db_session.session_scope() as session:
            nodes = session.query(Node).all()

        return [self.to_domain(n) for n in nodes]

    def exists(self, node_id) -> bool:
        with singletons.db_session.session_scope() as session:
            return session.query(exists().where(Node.id == node_id)).scalar()

    def to_domain(self, node: Node) -> EmulationNode:
        return singletons.simulation_manager.nodes_id_mapping[node.id]
