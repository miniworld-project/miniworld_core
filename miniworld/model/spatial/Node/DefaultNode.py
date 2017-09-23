# encoding: utf-8


from miniworld.model.spatial.MovementPattern.RandomWalk import RandomWalk
from .AbstractNode import AbstractNode

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class DefaultNode(AbstractNode):
    """
    Attributes
    ----------
    crnt_movement_pattern :                  AbstractMovementPattern
    dict_of_movement_pattern :               dict<String, AbstractMovementPattern>
    """

    def __init__(self, node_id):
        super(DefaultNode, self).__init__(node_id)
        self.crnt_movement_pattern = RandomWalk()
        self.dict_of_movement_pattern["RandomWalk"] = self.crnt_movement_pattern

    def __check_conditions(self):
        pass
