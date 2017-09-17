
# encoding: utf-8
from miniworld.model.singletons.Singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class Road:
    '''
    Parameter
    ---------
    singleton :     MovmentPattern
    start_id :      int
    end_id :        int
    car_reverse :   boolean
    car_quality :   int
    bike_reverse :  boolean
    bike_quality :  int
    foot_quality :  int

    Attributes
    ----------
    singleton :     MovmentPattern
    start_point :   MapNode
    end_point :     MapNode
    car_reverse :   boolean
    car_quality :   int
    bike_reverse :  boolean
    bike_quality :  int
    foot_quality :  int
    '''

    def __init__(self, start_id, end_id, car_reverse, car_quality, bike_reverse, bike_quality, foot_quality):
        self.start_point = singletons.spatial_singleton.get_node_for_id(start_id)
        self.end_point = singletons.spatial_singleton.get_node_for_id(end_id)
        self.car_reverse = car_reverse
        self.car_quality = car_quality
        self.bike_reverse = bike_reverse
        self.bike_quality = bike_quality
        self.foot_quality = foot_quality

    def get_car_quality(self):
        return self.car_quality

    def is_reverse_drivable_by_car(self):
        '''
        Returns
        -------
        boolean
        '''
        return self.car_reverse

    def is_reverse_drivable_by_bike(self):
        '''
        Returns
        -------
        boolean
        '''
        return self.bike_reverse

    def has_more_or_equal_qualitaty_for_car_then(self, quality):
        '''
        Parameter
        ---------
        quality : int

        Returns
        -------
        boolean
        '''
        return self.car_quality >= quality

    def has_more_or_equal_qualitaty_for_bike_then(self, quality):
        '''
        Parameter
        ---------
        quality : int

        Returns
        -------
        boolean
        '''
        return self.bike_quality >= quality

    def get_start_point(self):
        '''
        Returns
        -------
        MapNode
        '''
        return self.start_point

    def get_end_point(self):
        '''
        Returns
        -------
        MapNode
        '''
        return self.end_point

    def is_road_direct_rechable_from_given_point_with_quality_restrictions_for_cars(self, old_end_point, quality):
        '''
        Returns
        -------
        boolean
        '''
        return (old_end_point.getId() == self.start_point.getId() and self.has_more_or_equal_qualitaty_for_car_then(quality)) or \
               (old_end_point.getId() == self.end_point.getId() and self.has_more_or_equal_qualitaty_for_car_then(quality) and self.car_reverse)

    def is_road_direct_rechable_from_given_point_with_quality_restrictions_for_bike(self, old_end_point, quality):
        '''
        Returns
        -------
        boolean
        '''
        return (old_end_point is self.start_point and self.has_more_or_equal_qualitaty_for_bike_then(quality)) or \
               (old_end_point is self.end_point and self.has_more_or_equal_qualitaty_for_bike_then(quality) and self.bike_reverse)
