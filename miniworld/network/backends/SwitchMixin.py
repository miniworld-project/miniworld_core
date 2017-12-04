from collections import OrderedDict


# TODO: still needed?
class SwitchMixin:
    def create_switches(self):
        # create one switch for each node interface
        self.switches = OrderedDict(
            (_if, self.network_backend_bootstrapper.switch_type(self.node_id, _if)) for _if in self.interfaces
        )

    def start_switches(self, *args, **kwargs):
        for switch in self.switches.values():
            switch.start(*args, **kwargs)
