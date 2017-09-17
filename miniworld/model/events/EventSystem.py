import collections
import threading
from collections import OrderedDict
from contextlib import contextmanager
from threading import Lock

from ordered_set import OrderedSet

from miniworld.model.events.Event import Event
from miniworld.model.events.EventProgressStore import EventProgressStore
from miniworld.model.events.EventSystemStats import EventSystemStats
from miniworld.model.singletons import Resetable


class EventSystem(collections.UserDict, EventSystemStats, Resetable.Resetable):
    '''
    Thread-safe event system. The model is usable like a normal dict.
    The default value for non existing keys is: :py:class:`.NodeEventSystem`

    Attributes
    ----------
    data : dict<str, EventProgressStore>
        The events per node.
    events : list<str>
    ready : threading.event
        Use to block progress generation until the system is ready.
    '''

    EVENT_TOTAL_PROGRESS = "total_progress"

    def __init__(self, events):
        self.reset()
        self.lock = Lock()
        self.events.extend(events)

    #########################################
    # Resetable
    #########################################

    def reset(self):
        self.data = OrderedDict()
        self.events = []
        self.ready = threading.Event()

    #########################################
    # Magic methods
    #########################################

    def __getitem__(self, item):
        if item not in self.data:
            self.data[item] = EventProgressStore()

        return self.data[item]

    #########################################
    # Context Managers
    #########################################

    @contextmanager
    def event_init(self, event_name, init_ids=None, finish_ids=None):
        '''
        Provides a contextmanager for event updating.

        Parameters
        ----------
        event_name : str
            Name of the event.
        init_ids : list<str>, optional, (default is init all nodes)
            List of ids to initialize with 0.
        finish_ids : list<str>, optional, (default is finish all nodes)
            List of ids to update with 1.0 after the context manager exits.

        Examples
        --------
        >>> from miniworld.model.events.EventSystem import EventSystem
        >>> from miniworld.management.events.MyCLIEventDisplay import MyCLIEventDisplay
        >>> from miniworld.model.events.MyEventSystem import MyEventSystem
        >>> import time
        >>> es = EventSystem([MyEventSystem.EVENT_VM_BOOT])
        >>> # instead of constructor: es.events.add(es.EVENT_VM_BOOT)
        >>> #cli_display = MyCLIEventDisplay(es)
        >>> #cli_display.start_progress_thread()>>>
        >>> es.ready.set()
        >>> with es.event_init(MyEventSystem.EVENT_VM_BOOT) as event_boot:
        >>>     for i in range(5):
        >>>         time.sleep(0.2)
        >>>         event_boot.update([1], 0.2 * i)
        >>>         event_boot.update([2], 0.1 * i)
        >>>         print "%d: %s (%s)" % (i, es.get_progress(), es.items())
        >>>     # progress is not 100% yet
        >>>     time.sleep(5)
        >>>     # but after the context manager exits
        >>>     print "finishing ..."
        >>> print es.get_progress(), es.items(
        '''
        if init_ids is None:
            init_ids = list(self.keys())

        event = Event(event_name, self)
        event.init(init_ids)
        yield event

        # NOTE: do this after yielding, we may have new ids
        if finish_ids is None:
            finish_ids = list(self.keys())
        event.finish(finish_ids)

    def event_no_init_finish(self, event_name):
        '''
        Same as :py:meth:`.event` but do no init and no finish.
        '''
        return self.event_init(event_name, init_ids=[], finish_ids=[])

    def event_no_init(self, event_name, finish_ids=None):
        '''
        Same as :py:meth:`.event` but do no init.
        '''
        return self.event_init(event_name, init_ids=[], finish_ids=finish_ids)

    #########################################
    # EventSystemStats
    #########################################

    def get_average_complete_progress(self):
        '''
        Get the average complete progress.
        Therefore, the progress of all events divided by the number of events.

        Returns
        -------
        float
        '''
        cnt_events = len(self.get_events())
        if cnt_events > 0:
            return sum([self.get_average_progress(event) for event in self.get_events()]) * 1.0 / cnt_events
        return 0.0

    def get_average_progress(self, event=None):
        '''
        Get the average progress for the `event`.

        Parameters
        ----------
        event : str, optional (default is None)
            The event for which the. None means progress for all events.

        Returns
        -------
        float
        '''
        cnt_items = len(self)
        sum_progress = None

        if event == self.EVENT_TOTAL_PROGRESS:
            return self.get_average_complete_progress()

        if event is None:
            sum_progress = sum(map(lambda node: node.get_average_progress(), self.values()))
        else:
            sum_progress = self.get_sum_progress_event(event)

        if cnt_items > 0:
            return sum_progress * 1.0 / cnt_items

        return 0.0

    #########################################
    # Event-Progress Init
    #########################################

    def init_events(self, events):
        '''
        Init the `events`. This might be necessary if one wants to enforce the order given by `events`.
        Otherwise the order is the order in which the events are updated the first time.

        Parameters
        ----------
        events: list<str>
        '''
        for node_id in self.keys():
            for event in events:
                self.update_event(event, 0.0, node_ids=[node_id])

    # TODO: make dynamic
    # TODO: REMOVE?
    def init_events_for_node(self, node_id):
        for event in self.events:
            self.update_event(event, 0.0, node_ids=[node_id])

    #########################################
    # Event-Progress Getter
    #########################################

    def get_progress(self, asc=True):
        '''
        Get a list describing the progress of each event.

        Returns
        -------
        list<tuple<str, float>>
            Progress for each event.
        '''

        # block until system is ready
        while not self.ready.isSet():
            self.ready.wait(0.1)

        events = self.get_all_events()
        if not asc:
            events = reversed(list(events))

        return [(event, self.get_average_progress(event)) for event in events]

    def get_sum_progress_event(self, event):
        '''
        Get the sum of the progress for the `key` for each node.

        Parameters
        ----------
        event

        Returns
        -------
        float
        '''
        return sum(map(lambda node: node[event], self.values()))

    def get_all_events(self):
        '''
        Get all registered events plus the event for the total progress.
        Assume each node has the same events.

        Returns
        -------
        OrderedSet<str>
        '''
        s = OrderedSet([self.EVENT_TOTAL_PROGRESS])
        s.update(self.get_events())
        return s

    def get_events(self):
        '''
        Get all registered events.
        Assume each node has the same events.

        Returns
        -------
        OrderedSet<str>
        '''
        return self.events

    #########################################
    # Event updating
    #########################################

    def update_event(self, event, progress, add=False, node_ids=None, all_nodes=False):
        '''
        Update the `event` with `progress`. If `add`, add the value to the current progress.

        Either `node_id` or `all_nodes` must be supplied.

        Parameters
        ----------
        node_id : str
        event : str
        progress : float
            Maximum is 1.0
        add : bool, optional (default is False=
            Add the `progress` to the current progress.
        node_ids : list<str>, optional
        all_nodes : bool, optional

        Returns
        -------
        list<float>
            List of

        Raises
        ------
        ValueError
        '''

        updated_progress = []

        # prevent nasty errors
        if node_ids is not None and not isinstance(node_ids, list):
            raise ValueError("`node_ids` must be a list!")

        if node_ids is None and all_nodes is None:
            raise ValueError("Either `node_id` or `all_nodes` must be supplied.")
        node_ids = node_ids if node_ids is not None else list(self.keys())

        def check_progress(progress):
            if progress > 1.0:
                raise ValueError("Progress must be 0 <= progress <= 1.0!")

        def update(node_id):
            # store progress for event
            new_progress = progress
            if add:
                old_progress = self[node_id][event]
                new_progress += old_progress

            check_progress(new_progress)
            self[node_id][event] = new_progress

            return new_progress

        with self.lock:
            for node_id in node_ids:
                updated_progress.append(update(node_id))

        return updated_progress


if __name__ == '__main__':
    from miniworld.model.events.EventSystem import EventSystem
    from miniworld.model.events.MyEventSystem import MyEventSystem
    import time
    from pprint import pprint, pformat

    es = EventSystem([MyEventSystem.EVENT_VM_BOOT])
    # instead of constructor: es.events.add(es.EVENT_VM_BOOT)
    #cli_display = MyCLIEventDisplay(es)
    # cli_display.start_progress_thread()

    es.ready.set()
    with es.event_init(MyEventSystem.EVENT_VM_BOOT) as event_boot:
        for i in range(5):
            time.sleep(0.2)
            event_boot.update([1], 0.2 * i)
            event_boot.update([2], 0.1 * i)
            print("avg: %s" % dict(es.get_progress()))
            print("per node: %s" % pformat(es))
        # progress is not 100% yet
        time.sleep(5)
        # but after the context manager exits
        print("finishing ...")
    print(es.get_progress())
    pprint(es)
