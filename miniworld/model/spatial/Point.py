
# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class Point:
    def __init__(self, id, location):
        self.id = id
        self.location = location

    def getId(self):
        return self.id

    def get_distance_in_m(self, snd_node):
        return self.get_distance_in_km(snd_node) * 1000

    def get_distance_in_km(self, snd_node):
        return self.location.get_distance_in_km(snd_node.location)

    def get_heading(self, snd_node):
        return self.location.get_heading(snd_node.location)

    def get_lat(self):
        return self.location.get_lat_lon().to_string()[0]

    def get_lon(self):
        return self.location.get_lat_lon().to_string()[1]
