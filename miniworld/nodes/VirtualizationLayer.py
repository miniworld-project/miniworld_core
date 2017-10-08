from miniworld.errors import Base
from miniworld.model.StartableObject import ScenarioState
from miniworld.singletons import singletons


class VirtualizationLayer(ScenarioState):
    """
    Attributes
    ----------
    node : EmulationNode
        The associated Node.
    nlog
        Extra node logger.
    id : int
    """

    def __init__(self, id, emulation_node):
        self._logger = singletons.logger_factory.get_logger(self)
        ScenarioState.__init__(self)

        self.emulation_node = emulation_node

        # create extra node logger
        self.nlog = singletons.logger_factory.get_node_logger(id)

        self.id = id

    def reset(self):
        pass

    class InvalidImage(Base):
        pass
