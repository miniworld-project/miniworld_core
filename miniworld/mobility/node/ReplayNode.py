# encoding: utf-8
from miniworld.mobility.movement import ReplayMovementPattern
from miniworld.singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class ReplayNode():
    def __init__(self, node_id):
        self.crnt_movement_pattern = ReplayMovementPattern(singletons.spatial_singleton.file_path, node_id)

    def step(self):
        self.crnt_movement_pattern.walk()

    def get_lat(self):
        return self.crnt_movement_pattern.get_lat()

    def get_lon(self):
        return self.crnt_movement_pattern.get_lon()
