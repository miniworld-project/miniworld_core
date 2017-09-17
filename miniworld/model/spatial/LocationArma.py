__author__ = 'lampep'

import math


class LocationArma(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_lon(self):
        return self.x

    def get_lat(self):
        return self.y

    def get_distance_in_km(self, snd_location):
        """
        Parameters
        ----------
        snd_location : Location

        Returns
        -------
        int
        """
        return self.get_distance_in_m(snd_location) / 1000

    def get_distance_in_m(self, snd_location):
        """
        Parameters
        ----------
        snd_location : Location

        Returns
        -------
        int
        """
        return math.sqrt((self.x - snd_location.location.x) ** 2 + (self.y - snd_location.location.y) ** 2)
