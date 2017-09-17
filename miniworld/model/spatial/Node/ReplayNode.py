
# encoding: utf-8
from miniworld.model.singletons.Singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from miniworld.model.spatial.MovementPattern.ReplayMovementPattern import ReplayMovementPattern


class ReplayNode():
    def __init__(self, node_id):
        self.crnt_movement_pattern = ReplayMovementPattern(singletons.spatial_singleton.file_path, node_id)

    def step(self):
        self.crnt_movement_pattern.walk()

    def get_lat(self):
        return self.crnt_movement_pattern.get_lat()

    def get_lon(self):
        return self.crnt_movement_pattern.get_lon()
