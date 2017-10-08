import enum
import uuid


class Resource(enum.Enum):
    emulation = 'emulation'
    node = 'node'


class Type(enum.Enum):
    read = 'read'
    write = 'write'


class LockEntry:
    def __init__(self, type: Type):
        self.type = type
        self.id = uuid.uuid4()

    def __repr__(self):
        return f'{self.__class__.__name__}({self.type!r}, {self.id!r})'

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id
