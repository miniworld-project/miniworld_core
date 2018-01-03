from typing import List

from miniworld.model.base import Base
from miniworld.model.domain.interface import Interface
from miniworld.network.connection import AbstractConnection


class Node(Base):
    def __init__(self,
                 _id: int = None,
                 interfaces: List[Interface] = None,
                 type: AbstractConnection.ConnectionType = None
                 ):
        super().__init__()
        self._id = _id
        self.interfaces = interfaces
        self.type = type
