from miniworld.model.StartableObject import ScenarioStateReset
from miniworld.model.base import Base
from miniworld.model.domain.node import Node
from miniworld.singletons import singletons


class AbstractNode(Base, ScenarioStateReset):
    def __init__(self, node: Node):
        Base.__init__(self)
        ScenarioStateReset.__init__(self)

        self._node = node
        self._logger = singletons.logger_factory.get_logger(self)
