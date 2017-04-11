
# encoding: utf-8

__author__ = "Patrick Lampe"
__email__ = "uni at lampep.de"

from LatLon23 import LatLon, Latitude, Longitude

class Location:
    ''' 
    Parameters
    ----------
    lat : LatLon.lat
    lon : LatLon.lon
    
    Attributes
    ----------
    latlon : LatLon
    '''
    def __init__(self, lat, lon):
        self.latlon = LatLon(Latitude(lat), Longitude(lon))

    def get_distance_in_km(self, snd_location):
        '''
        Parameters
        ----------
        snd_location : Location
        
        Returns
        -------
        int
        '''
        return self.latlon.distance(snd_location.latlon)
      
    def get_distance_in_m(self, snd_location):
        '''
        Parameters
        ----------
        snd_location : Location
        
        Returns
        -------
        int
        '''
        return self.get_distance_in_km(snd_location)*1000
        
    def get_heading(self, snd_location):
        '''
        Parameters
        ----------
        snd_location : Location
        
        Returns
        -------
        LatLon.heading
        '''
        return self.latlon.heading_initial(snd_location.latlon)
        
    def get_lat_lon(self):
        '''
        Returns
        -------
        LatLon
        '''
        return self.latlon
        
    def lat_lon_to_string(self):
        '''
        Returns
        -------
        String
        '''
        return self.latlon.to_string('D')    
        
    def offset_in_m(self, heading, distance):
        '''
        Parameters
        ----------
        heading : LatLon.heading
        distance : int
        
        Returns
        -------
        Location
        '''
        latlon = self.latlon.offset(heading, distance/1000)
        return  Location(latlon.to_string('D')[0], latlon.to_string('D')[1])
    