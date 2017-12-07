import enum
from typing import Dict

from miniworld.model.StartableObject import ScenarioStateReset
from miniworld.model.domain.connection import Connection


class ConnectionServiceBase(ScenarioStateReset):
    def start(self, connection: Connection):
        """
        Start the connection.
        """
        raise NotImplementedError

    def adjust_link_quality(self, connection: Connection, link_quality_dict: Dict):
        raise NotImplementedError


class AbstractConnection:
    class ConnectionType(enum.Enum):
        user = 'user'
        mgmt = 'mgmt'
        central = 'central'
