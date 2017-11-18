from sqlalchemy import exists

from miniworld.model.db.base import Node
from miniworld.singletons import singletons


class NodePersistenceService:
    def add(self, node: Node) -> Node:
        with singletons.db_session.session_scope() as session:
            session.add(node)
            session.commit()

        return node

    def exists(self, node_id) -> bool:
        with singletons.db_session.session_scope() as session:
            return session.query(exists().where(Node.id == node_id)).scalar()
