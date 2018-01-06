# encoding: utf-8


from miniworld.mobility.movement.MoveOnBigStreets import MoveOnBigStreets
from .AbstractNode import AbstractNode

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class MoveOnBigStreetsNode(AbstractNode):
    """
    Attributes
    ----------
    crnt_movement_pattern :                  AbstractMovementPattern
    dict_of_movement_pattern :               dict<String, AbstractMovementPattern>
    """

    def __init__(self, crnt_node_id_in_type):
        super(MoveOnBigStreetsNode, self).__init__(crnt_node_id_in_type)
        self.crnt_movement_pattern = MoveOnBigStreets()
        self.dict_of_movement_pattern["MoveOnBigStreets"] = self.crnt_movement_pattern

    def __check_conditions(self):
        pass
