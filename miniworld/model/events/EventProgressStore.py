import collections
from collections import OrderedDict

from miniworld.model.events.EventSystemStats import EventSystemStats


class EventProgressStore(collections.UserDict, EventSystemStats):
    """
    Stores the progress for some events.
    Can be used like a normal dictionary. The default value for non-existing keys is 0.
    The order is insertion-based.

    Attributes
    -----------
    data : dict<str, float>
        Event, progress.
    """

    def __init__(self):
        self.data = OrderedDict()

    #########################################
    # Magic Methods
    #########################################

    def __getitem__(self, item):
        if item not in self.data:
            self.data[item] = 0.0

        return self.data[item]

    #########################################
    # EventSystemStats
    #########################################

    def get_average_progress(self):
        cnt_items = len(self)
        sum_progress = sum(self.values())
        if cnt_items > 0:
            return sum_progress * 1.0 / cnt_items
        return 0
