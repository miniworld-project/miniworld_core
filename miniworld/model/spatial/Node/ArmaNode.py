
# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

import random

from miniworld.model.spatial.LocationArma import LocationArma
from .AbstractNode import AbstractNode


class ArmaNode(AbstractNode):
    def __init__(self, crnt_node_id_in_type):
        self.location = LocationArma(0, 0)

        def r(): return random.randint(0, 255)
        self.color = '#%02X%02X%02X' % (r(), r(), r())

    def walk(self, step):
        x, y = step
        self.location = LocationArma(y, x)  # self.location.offset_in_m(heading, distance)

    def get_distance_in_m(self, snd_node):
        return self.location.get_distance_in_m(snd_node)

    def get_distance_in_km(self, snd_node):
        return self.location.get_distance_in_km(snd_node)

    def get_lon(self):
        return self.location.get_lon()

    def get_lat(self):
        return self.location.get_lat()
