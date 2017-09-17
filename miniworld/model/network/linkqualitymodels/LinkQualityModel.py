import importlib
import sys

from miniworld import log
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import *

VAL_DISTANCE_ZERO = 0
VAL_DISTANCE_UNLIMITED = sys.maxsize

__author__ = 'Nils Schmidt'

# TODO: DOC


class LinkQualityModel:

    def __init__(self,
                 # link quality stuff
                 bandwidth=None,
                 loss=None,
                 **kwargs):
        '''
        Parameters
        ----------
        bandwidth : int, optional (default is unlimited)
            Bandwidth in bytes/sec. `LINK_QUALITY_VAL_BANDWIDTH_UNLIMITED` means unlimited.
        loss : int, optional (default is no loss)
        max_connected_distance : float

        '''
        if loss is None:
            loss = LINK_QUALITY_VAL_LOSS_NONE
        if bandwidth is None:
            bandwidth = LINK_QUALITY_VAL_BANDWIDTH_UNLIMITED

        self.loss = loss
        self.bandwidth = bandwidth
        self.max_connected_distance = None

        self.precalculate()

    def precalculate(self):

        log.info("precalculating link qualities ...")
        for distance in range(0, sys.maxsize):
            connected, link_quality_dict = self.distance_2_link_quality(distance)
            if not connected:
                self.max_connected_distance = distance
                log.info("max_connected_distance: '%s'", self.max_connected_distance)
                break

        if self.max_connected_distance is None:
            raise RuntimeError("Maximum connected distance could not be calculated!")

    @staticmethod
    def import_link_quality_model(pn):
        '''
        Import a :py:class:`.LinkQualityModel` by package name.

        Parameters
        ----------
        pn : str
            Full package name of the class to import. E.g. "a.b.c"

        Returns
        -------
        type

        Raises
        ------
        ValueError
        '''
        mod = '.'.join(pn.split(".")[:-1])
        cls = pn.split(".")[-1]
        print(mod, cls)

        try:
            module = importlib.import_module(mod)

            try:
                clazz = getattr(module, cls)

                if isinstance(clazz, LinkQualityModel.__class__):
                    return clazz
                else:
                    raise ValueError("Class must be a subclass of '%s'" % LinkQualityModel.__class__.__name__)

            except AttributeError:
                raise ValueError("Class '%s' not found in module '%s'!" % (cls, mod))

        except ImportError:
            raise ValueError("Module '%s' not found!" % mod)

    #####################################################
    # Implement these methods in a subclass
    #####################################################

    # TODO: DOC
    # TODO: REMOVE 1st ARG?
    def get_initial_link_quality(self):
        return False, {
            LINK_QUALITY_KEY_BANDWIDTH: self.bandwidth,
            LINK_QUALITY_KEY_LOSS: self.loss
        }

    # TODO: DOC: idempotent!
    # TODO: REMOVE 1st ARG?

    def distance_2_link_quality(self, distance):

        distance = round(distance)
        return self._distance_2_link_quality(distance)

    def _distance_2_link_quality(self, distance):
        '''
        Returns
        -------
        bool, dict
            If connected, the link quality described by certain attributes such as e.g. bandwidth, loss, ...
        '''

        raise NotImplementedError
