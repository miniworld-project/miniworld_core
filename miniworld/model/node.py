from typing import List

from miniworld.model.base import Base
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.connection import Connection


class EmulationNode(Base):
    def __init__(self,
                 id: int = None,
                 interfaces: Interfaces = None,
                 connections: List[Connection] = None,
                 type: Connection.ConnectionType = None
                 ):
        super().__init__()
        self.id = id
        self.interfaces = interfaces
        self.connections = connections
        self.type = type
