from miniworld.errors import Base


class REPLError(Base):
    pass


class REPLUnexpectedResult(REPLError):
    pass


class REPLTimeout(REPLError):
    pass