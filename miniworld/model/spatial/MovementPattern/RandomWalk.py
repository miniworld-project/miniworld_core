# encoding: utf-8
from miniworld.Constants import PATH_MARBURG_OSM_MAP
from miniworld.model.singletons.Singletons import singletons

import sqlite3
from random import randint

from miniworld.model.spatial.Point import Point
from miniworld.model.spatial.Location import Location
from miniworld.model.spatial.MovementPattern.AbstractMovementPattern import AbstractMovementPattern

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


# TODO: PATRICK: REFACTOR! USE PYTHON SPATIAL OBJECTS INSTEAD OF DB STUFF!
# TODO: if not connection created in each function, a sqlite thread error appears :/


class RandomWalk(AbstractMovementPattern):
    def __init__(self):
        self.conn = sqlite3.connect(PATH_MARBURG_OSM_MAP)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT COUNT(*) FROM nodes")
        self.count_nodes = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM edges")
        self.count_edges = self.cursor.fetchone()[0]
        super(RandomWalk, self).__init__()

    def get_start_point(self):
        index = randint(0, self.count_nodes - 1)
        conn = sqlite3.connect(PATH_MARBURG_OSM_MAP)
        cursor = conn.cursor()
        cursor.execute("SELECT original_id, lat, lon FROM nodes WHERE id=:index", {"index": index})
        original_id, lat, lon = cursor.fetchone()
        map_node = Point(original_id, Location(lat, lon))
        if (map_node is None or self.get_next_map_node(map_node, None) is None):
            return self.get_start_point()
        else:
            return map_node

    def get_next_map_node(self, crt_map_node, last_map_node):
        conn = sqlite3.connect(PATH_MARBURG_OSM_MAP)
        cursor = conn.cursor()
        if (last_map_node is None):
            cursor.execute(
                "SELECT COUNT(*) FROM (SELECT target AS id FROM edges WHERE source=:index UNION SELECT source AS id FROM edges WHERE target=:index)",
                {"index": crt_map_node.getId()})
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM (SELECT target AS id FROM edges WHERE source=:index AND target!=:index_last UNION SELECT source AS id FROM edges WHERE target=:index AND source!=:index_last) ",
                {"index": crt_map_node.getId(), "index_last": last_map_node.getId()})
        edges = cursor.fetchone()[0]
        bool_ = False

        if (edges == 0):
            bool_ = True
            cursor2 = conn.cursor()
            cursor2.execute(
                "SELECT COUNT(*) FROM (SELECT target AS id FROM edges WHERE source=:index UNION SELECT source AS id FROM edges WHERE target=:index)",
                {"index": crt_map_node.getId()})
            edges = cursor2.fetchone()[0]

        if (edges > 0):
            if (edges == 1):
                index = 0
            else:
                index = randint(0, edges - 1)
            for_cursor = conn.cursor()
            if (last_map_node is None or bool_):
                for_cursor.execute(
                    "SELECT source AS id FROM edges WHERE target=:index UNION SELECT target AS id FROM edges WHERE source=:index",
                    {"index": crt_map_node.getId()})
            else:
                for_cursor.execute(
                    "SELECT source AS id FROM edges WHERE target=:index AND source!=:index_last UNION SELECT target AS id FROM edges WHERE source=:index AND target!=:index_last",
                    {"index": crt_map_node.getId(), "index_last": last_map_node.getId()})
            target = for_cursor.fetchall()[index][0]
            return self.__getMapNodeForOriginalId(target)
        else:
            return None

    def __getMapNodeForOriginalId(self, original_id):
        return singletons.spatial_singleton.get_node_for_id(original_id)

    def get_speed(self):
        return randint(1, 5)
