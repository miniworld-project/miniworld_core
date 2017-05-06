from miniworld.errors import Base
from miniworld.log import get_node_logger
from miniworld.model.StartableObject import StartableSimulationStateObject


class VirtualizationLayer(StartableSimulationStateObject):

    '''
    Attributes
    ----------
    node : EmulationNode
        The associated Node.
    nlog
        Extra node logger.
    id : int
    '''
    def __init__(self, id, emulation_node):
        StartableSimulationStateObject.__init__(self)

        self.emulation_node = emulation_node

        # create extra node logger
        self.nlog = get_node_logger(id)

        self.id = id

    def reset(self):
        pass

    class InvalidImage(Base):
        pass