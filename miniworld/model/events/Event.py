class Event(object):

    def __init__(self, event, event_system):
        """
        Helper class for the :py:class:`.EventSystem` to provide a context manager for a event.

        Parameters
        ----------
        event : str
        event_system : EventSystem
        """
        self.event = event
        self.event_system = event_system

    def update(self, node_ids, progress, **kwargs):
        self.event_system.update_event(self.event, progress, node_ids=node_ids, **kwargs)

    def update_all(self, progress, **kwargs):
        self.event_system.update_event(self.event, progress, all_nodes=True, **kwargs)

    def init(self, node_ids, **kwargs):
        self.event_system.update_event(self.event, 0.0, node_ids=node_ids, **kwargs)

    def init_all(self, **kwargs):
        self.event_system.update_event(self.event, 0.0, all_nodes=True, **kwargs)

    def finish(self, node_ids, **kwargs):
        self.event_system.update_event(self.event, 1.0, node_ids=node_ids, **kwargs)

    def finish_all(self, **kwargs):
        self.event_system.update_event(self.event, 1.0, all_nodes=True, **kwargs)
