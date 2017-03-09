# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from time import strptime

class ArmaMovementPattern(object):
    def __init__(self, file_path, node_id):
        self.file = open(file_path, "r")
        self.node_id = node_id
        self.crnt_line = ""
        self.next_step = self.get_next_step_from_file()

    def __get_next_step_from_file(self):
        while("POSITIONLIST_BEGIN" not in self.file.readline()):
            pass

        self.crnt_line = self.file.readline()
        next_time = self.__extract_time_from_line(self.crnt_line)
        list_of_coordinates = []
        while("POSITIONLIST_END" not in self.crnt_line):
            list_of_coordinates.append(self.__extract_coordinates_from_line(self.crnt_line))
            self.crnt_line = self.file.readline()
        self.next_step = (next_time, list_of_coordinates)
        
    def __extract_coordinates_from_line(self, line):
        first_index = line.find("\"[") + 2
        second_index =line.find("]\"")
        coordinates = line[first_index:second_index]
        list_of_cords = coordinates.split(",")
        return (float(list_of_cords[0]), float(list_of_cords[1]))

    def __extract_time_from_line(self, line):
        return strptime(line[0:7], "%H:%M:%S")

    def walk(self):
        self.__get_next_step_from_file()

    def get_lat(self):
        list_of_coordinates = self.next_step[1]
        return list_of_coordinates[self.node_id][0]

    def get_lon(self):
        list_of_coordinates = self.next_step[1]
        return list_of_coordinates[self.node_id][1]