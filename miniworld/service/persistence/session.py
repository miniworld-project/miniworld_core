import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from miniworld.model.db.base import Base


class Session:
    def __init__(self):
        self.engine = None
        self.session = None

    def create_session(self):
        self.engine = create_engine('sqlite:///:memory:', echo=False, connect_args={'check_same_thread': False},
                                    poolclass=StaticPool)  # type: Engine
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_schema(self):
        Base.metadata.create_all(self.engine)

    def delete_schema(self):
        Base.metadata.drop_all(self.engine)

    def clear_state(self):
        self.delete_schema()
        self.create_schema()

    @contextlib.contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
