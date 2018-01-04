from typing import Dict

from miniworld.model.base import Base


class Connection(Base):
    def __init__(self,
                 _id: int = None,
                 emulation_node_x: 'EmulationNode' = None,
                 emulation_node_y: 'EmulationNode' = None,
                 interface_x: 'Interface' = None,
                 interface_y: 'Interface' = None,
                 connection_type: 'AbstractConnection.ConnectionType' = None,
                 is_remote_conn: bool = None,
                 impairment: Dict = None,
                 connected: bool = None,
                 step_added: int = None,
                 distance: float = None
                 ):
        Base.__init__(self)
        self._id = _id
        self.emulation_node_x = emulation_node_x
        self.emulation_node_y = emulation_node_y
        self.interface_x = interface_x
        self.interface_y = interface_y
        self.connection_type = connection_type
        self.is_remote_conn = is_remote_conn
        self.impairment = impairment
        self.connected = connected
        self.step_added = step_added
        self.distance = distance

    @classmethod
    def from_connection_info(cls, emulation_node_x, emulation_node_y, interface_x, interface_y,
                             connection_info: 'ConnectionInfo'):
        return cls(
            emulation_node_x=emulation_node_x, emulation_node_y=emulation_node_y,
            interface_x=interface_x, interface_y=interface_y,
            connection_type=connection_info.connection_type,
            is_remote_conn=connection_info.is_remote_conn,
            step_added=connection_info.step_added,
            distance=connection_info.distance
        )
