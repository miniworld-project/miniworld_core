from miniworld.model.StartableObject import ScenarioState
from miniworld.model.base import Base
from miniworld.model.domain.node import Node
from miniworld.singletons import singletons


class AbstractNode(Base, ScenarioState):
    def __init__(self, node: Node):
        Base.__init__(self)
        ScenarioState.__init__(self)

        self._node = node
        self._logger = singletons.logger_factory.get_logger(self)
