# encoding: utf-8

from miniworld.model.singletons.Singletons import singletons

from collections import OrderedDict
import geojson
from .Road import Road

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class Roads:
    """
    Attributes
    ----------
    list_of_roads :                                                 list
    feature_coll_roads :                                            FeatureCollection
    geo_json :                                                      geojson
    list_of_roads_with_quality_more_or_equal_than_one_for_car :     list
    list_of_roads_with_quality_more_or_equal_than_one_for_bike :    list
    """

    def __init__(self):
        cursor = singletons.spatial_singleton.get_connection_to_database().cursor()
        cursor.execute("SELECT source, target, car_rev, car, bike_rev, bike, foot FROM edges")
        self.list_of_roads = [self.__convert_sql_line_to_road(line) for line in cursor.fetchall()]
        self.feature_coll_roads = geojson.FeatureCollection(
            [self.__get_geo_json_object_for_road(road) for road in self.list_of_roads])
        self.geo_json = geojson.dumps(self.feature_coll_roads)
        self.list_of_roads_with_quality_more_or_equal_than_one_for_car = [road for road in self.list_of_roads if
                                                                          road.has_more_or_equal_qualitaty_for_car_then(
                                                                              1)]
        self.list_of_roads_with_quality_more_or_equal_than_one_for_bike = [road for road in self.list_of_roads if
                                                                           road.has_more_or_equal_qualitaty_for_bike_then(
                                                                               1)]

    def get_geo_json(self):
        """
        Returns
        -------
        geo_json
                    of all existing roads
        """
        return self.geo_json

    def get_list_of_roads_with_quality_more_or_equal_than_x_for_car(self, quality):
        """
        Parameters
        ----------
        quality : int

        Returns
        -------
        list
        """
        return [road for road in self.list_of_roads if road.has_more_or_equal_qualitaty_for_car_then(quality)]

    def get_list_of_roads_with_quality_more_or_equal_than_x_for_bike(self, quality):
        """
        Parameters
        ----------
        quality : int

        Returns
        -------
        list
        """
        return [road for road in self.list_of_roads if road.has_more_or_equal_qualitaty_for_bike_then(quality)]

    def get_list_of_next_roads_with_quality_restriction_for_cars(self, end_point, quality):
        """
        Parameters
        ----------
        quality : int

        Returns
        -------
        list
        """
        return [road for road in self.list_of_roads if
                road.is_road_direct_rechable_from_given_point_with_quality_restrictions_for_cars(end_point, quality)]

    def get_list_of_next_roads_with_quality_restriction_for_bike(self, end_point, quality):
        """
        Parameters
        ----------
        end_point : MapNode

        Returns
        -------
        list
        """
        return [road for road in self.list_of_roads if
                road.is_road_direct_rechable_from_given_point_with_quality_restrictions_for_bike(end_point, quality)]

    def __convert_sql_line_to_road(self, line):
        return Road(line[0], line[1], line[2], line[3], line[4], line[5], line[6])

    def __get_geo_json_object_for_road(self, road):
        source = road.get_start_point()
        target = road.get_end_point()
        quality = road.get_car_quality()

        return OrderedDict(
            type="Feature",
            geometry=OrderedDict(
                type="LineString",
                coordinates=[[float(source.get_lon()), float(source.get_lat())],
                             [float(target.get_lon()), float(target.get_lat())]]
            ),
            properties=OrderedDict(
                type=str(quality),
                name="Coors Field",
                amenity="Baseball Stadium"
            )
        )
