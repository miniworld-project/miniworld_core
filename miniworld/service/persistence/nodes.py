from sqlalchemy import exists
from typing import List

from miniworld.model.db.base import Node
from miniworld.nodes.EmulationNode import EmulationNode
from miniworld.singletons import singletons


class NodePersistenceService:
    def add(self, node: Node) -> Node:
        with singletons.db_session.session_scope() as session:
            for interface in node.interfaces:
                session.add(interface)
            session.add(node)
            session.commit()

        return node

    def all(self) -> List[EmulationNode]:
        with singletons.db_session.session_scope() as session:
            nodes = session.query(Node).all()

        return [self.to_domain(n) for n in nodes]

    def exists(self, node_id) -> bool:
        with singletons.db_session.session_scope() as session:
            return session.query(exists().where(Node.id == node_id)).scalar()

    def to_domain(self, node: Node) -> EmulationNode:
        return singletons.simulation_manager.nodes_id_mapping[node.id]
