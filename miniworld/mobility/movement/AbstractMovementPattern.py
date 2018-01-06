# encoding: utf-8


from miniworld.singletons import singletons

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"


class AbstractMovementPattern:
    def __init__(self):
        self.current_map_node = self.get_start_point()
        self.location = self.current_map_node.location
        self.speed_in_m_per_s = self.get_speed()
        self.next_map_node = self.get_next_map_node(self.current_map_node, None)
        if self.next_map_node is not None:
            self.distance_to_next_map_node_in_m = self.current_map_node.get_distance_in_m(self.next_map_node)
            self.heading = self.current_map_node.get_heading(self.next_map_node)

    def get_next_map_node(self, crt_map_node, last_map_node):
        raise NotImplementedError("Should have implemented this")

    def get_speed(self):
        raise NotImplementedError("Should have implemented this")

    def get_start_point(self):
        """
        Returns
        -------
        Point
        """
        return singletons.spatial_singleton.get_random_point()

    def get_name(self):
        """
        Returns
        -------
        String
            Name of the class this methode is call in
        """
        return self.__class__.__name__

    def walk(self):
        """
        Parameters
        ----------
        seconds         float

        changes the location stored in the movement_pattern
        """
        self.__walk_m(singletons.spatial_singleton.seconds_per_simulation_step * self.speed_in_m_per_s)

    def get_lat(self):
        """
        Returns
        -------
        LatLon.lat
        """
        return self.location.lat_lon_to_string()[0]

    def get_lon(self):
        """
        Returns
        -------
        LatLon.lon
        """
        return self.location.lat_lon_to_string()[1]

    def __walk_m(self, distance_in_m):
        if (self.next_map_node is not None and distance_in_m < self.distance_to_next_map_node_in_m):
            self.location = self.location.offset_in_m(self.heading, float(distance_in_m))
            self.distance_to_next_map_node_in_m = self.distance_to_next_map_node_in_m - distance_in_m
        else:
            if (self.next_map_node is not None and self.distance_to_next_map_node_in_m is not None):
                distance_to_go = distance_in_m - self.distance_to_next_map_node_in_m
                last_map_node = self.current_map_node
                self.current_map_node = self.next_map_node
                self.location = self.current_map_node.location
                self.next_map_node = self.get_next_map_node(self.current_map_node, last_map_node)
                if (self.next_map_node is not None):
                    self.distance_to_next_map_node_in_m = self.current_map_node.get_distance_in_m(self.next_map_node)
                    self.heading = self.current_map_node.get_heading(self.next_map_node)
                    self.__walk_m(distance_to_go)
