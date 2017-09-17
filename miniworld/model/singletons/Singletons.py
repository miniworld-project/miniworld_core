__author__ = 'Nils Schmidt'


# TODO: #54,#55: adjust doc
class Singletons:
    '''
    Stores all singletons.
    The module `SingletonInit` shall be used to initialize them. Therefore, we prevent cyclic imports.
    Singletons which have state that shall be resetted when a new simulation is started, needs to
    be registered with `reset_simulation_scenario_state`.
    These singletons shall implement the `Resettable` interface.

    Attributes
    ----------
    event_system : EventSystem
    '''

    def __init__(self):
        super(Singletons, self).__init__()

        # TODO: DOC
        self.network_manager = None
        self.shell_helper = None
        self.spatial_singleton = None
        self.simulation_manager = None
        self.network_backend = None
        self.event_system = None
        self.simulation_state_gc = None
        self.simulation_errors = None
        self.protocol = None
        self.zeromq_server = None
        self.node_distribution_strategy = None
        self.qemu_process_singletons = None

# TODO: #54,#55: EXTRACT CLASS
#################################################
# Singleton reference
#################################################


singletons = Singletons()

if __name__ == '__main__':
    class Foo():
        def reset_simulation_state(self):
            print("reset")

    singletons.simulation_state_gc.add_singleton_with_simulation_scenario_state_(Foo())
    singletons.simulation_state_gc.reset_simulation_scenario_state()
