
# encoding: utf-8
import os
from miniworld.Constants import PATH_MARBURG_OSM_MAP
from miniworld.model.singletons.Resetable import Resetable

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

import sqlite3
import os
from random import randint
from miniworld.model.spatial.Point import Point
from miniworld.model.spatial.Location import Location


# TODO: also singleton for other backend stuff? move to other place?
class Singleton(Resetable):
    def __init__(self):

        # TODO: DOC created later ...

        PATH_MARBURG_OSM_MAP = "osm_marburg.db"
        self.reset()
        self.conn = sqlite3.connect(os.path.abspath(PATH_MARBURG_OSM_MAP))

        cursor = self.conn.cursor()
        for row in cursor.execute("SELECT original_id FROM nodes"):
            self.dict_of_all_points[row[0]] = self.__get_point_for_original_id(row[0])

    #########################################
    ### Resettable Interface
    #########################################

    def reset(self):
        self.roads = None
        self.file_path = ""

        self.dict_of_all_points = {}
        self.seconds_per_simulation_step = 1.0
        self.list_of_simulated_steps = []

    #########################################
    ### Other stuff
    #########################################


    def get_connection_to_database(self):
        return self.conn

    def set_seconds_per_simultion_step(self, seconds):
        self.seconds_per_simulation_step = seconds

    def add_next_simulated_step(self, current_simulation_step):
        self.list_of_simulated_steps.append(current_simulation_step)

    def get_roads(self):
        return self.roads
    
    def set_file_path(self, file_path):
        self.file_path = file_path
        self.add_file_path_to_list(file_path)
    
    def get_node_for_id(self, id):
        return self.dict_of_all_points[id]

    def get_random_point(self):
        count = len(self.dict_of_all_points.items())
        index = randint(0, count - 1)
        return self.dict_of_all_points.items()[index][1]



    def __get_point_for_original_id(self, original_id):
        cur = self.conn.cursor()
        cur.execute("SELECT lat, lon FROM nodes WHERE original_id=:index", {"index": original_id})
        lat, lon =  cur.fetchone()
        location = Location(lat, lon)
        return Point(original_id, location)