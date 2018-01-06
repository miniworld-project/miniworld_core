import contextlib

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from miniworld.model.db.base import Base
from miniworld.singletons import singletons


class Session:
    def __init__(self):
        self.engine = None
        self.session = None
        self._logger = singletons.logger_factory.get_logger(self)

    def create_session(self):
        self.engine = create_engine('sqlite:///db.sql', echo=False, connect_args={'check_same_thread': False},
                                    poolclass=StaticPool)  # type: Engine
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

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
