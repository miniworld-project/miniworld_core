# encoding: utf-8


import random

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class AbstractNode:
    """
    Parameter
    ---------

    Attributes
    ----------

    """

    def __init__(self, node_id):
        self.crnt_movement_pattern = None
        self.dict_of_movement_pattern = {}
        self.node_id = node_id

        def r():
            return random.randint(0, 255)

        self.color = '#%02X%02X%02X' % (r(), r(), r())

    def get_name_of_movement_patter(self, movement_pattern):
        return ""  # self.crnt_movement_pattern.get_name()

    def get_distance_in_m(self, snd_node):
        """
        Parameters
        ----------
        snd_node : Node

        Returns
        -------

        """
        return self.get_distance_in_km(snd_node) * 1000

    def get_distance_in_km(self, snd_node):
        """
        Parameters
        ----------
        snd_node : Node

        Returns
        -------

        """
        return self.crnt_movement_pattern.location.get_distance_in_km(snd_node.crnt_movement_pattern.location)

    def get_lat(self):
        """
        Returns
        -------
        LatLon.lat
        """
        return self.crnt_movement_pattern.get_lat()

    def get_lon(self):
        """
        Returns
        -------
        LatLon.lon
        """
        return self.crnt_movement_pattern.location.get_lat_lon().to_string()[1]

    def step(self):
        """
        Parameters
        ----------
        seconds : float
        """
        self.__check_conditions()
        self.crnt_movement_pattern.walk()

    def __check_conditions(self):
        pass
        # TODO:
        # raise NotImplementedError( "Should have implemented this" )
