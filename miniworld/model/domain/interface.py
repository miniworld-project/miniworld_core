import enum

from miniworld.model.base import Base


class Interface(Base):
    class InterfaceType(enum.Enum):
        mesh = 'mesh'
        ap = 'ap'
        adhoc = 'adhoc'
        bluetooth = 'bluetooth'
        wifidirect = 'wifidirect'
        hub = 'hub'
        management = 'management'

    INTERFACE_TYPE_NORMAL = {
        InterfaceType.ap,
        InterfaceType.mesh,
        InterfaceType.adhoc,
        InterfaceType.bluetooth,
        InterfaceType.wifidirect
    }

    def __init__(self,
                 _id: int = None,
                 name: str = None,
                 nr_host_interface: int = None,
                 ipv4: str = None,
                 ipv6: str = None,
                 mac: str = None
                 ):
        super().__init__()
        self._id = _id
        self.name = name
        self.nr_host_interface = nr_host_interface
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.mac = mac

        if name is not None:
            # validate name
            Interface.InterfaceType(name)
        self.name = name

    @property
    def class_id(self) -> int:
        return list(Interface.InterfaceType).index(Interface.InterfaceType(self.name))
