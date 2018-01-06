from miniworld.errors import Base
from miniworld.model.StartableObject import ScenarioState
from miniworld.model.domain.node import Node
from miniworld.singletons import singletons


class VirtualizationLayer(ScenarioState):
    def __init__(self, node: Node):
        self._logger = singletons.logger_factory.get_logger(self)
        ScenarioState.__init__(self)

        self.node = node

        # create extra node logger
        self.nlog = singletons.logger_factory.get_node_logger(self.node._id)

    def reset(self):
        pass

    class InvalidImage(Base):
        pass
