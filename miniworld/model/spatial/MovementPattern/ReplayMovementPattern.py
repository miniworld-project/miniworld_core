# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from miniworld.model.spatial.Location import Location

class ReplayMovementPattern:
    def __init__(self, file_path, node_id):
        self.file = open(file_path, "r")
        self.node_id = node_id
        self.location = None

    def get_next_step_from_file(self):
        crnt_line = self.file.readline()
        list_of_coordinates = self.__extract_coordinates_from_line(crnt_line)
        return Location(list_of_coordinates[self.node_id][0], list_of_coordinates[self.node_id][1])

    def walk(self):
        self.location = self.get_next_step_from_file()

    def get_lat(self):
        return self.location.lat_lon_to_string()[0]

    def get_lon(self):
        return self.location.lat_lon_to_string()[1]

    def __extract_coordinates_from_line(self, line):
        pass