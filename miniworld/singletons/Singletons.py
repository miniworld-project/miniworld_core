__author__ = 'Nils Schmidt'


class Singletons:
    """
    Stores all singletons.
    The module `SingletonInit` shall be used to initialize them. Therefore, we prevent cyclic imports.
    Singletons which have state that shall be resetted when a new simulation is started, needs to
    be registered with `reset_simulation_scenario_state`.
    These singletons shall implement the `Resettable` interface.
    """

    def __init__(self):
        super(Singletons, self).__init__()

        self.logger_factory = None  # type: LoggerFactory
        self.lock_manager = None
        self.logger = None  # type: logging.Logger

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
        self.network_backend_bootstrapper_factory = None

        # the object is a singleton during a scenario
        self.network_backend_bootstrapper = None

        self.scenario_config = None
        self.config = None
        self.db_session = None


#################################################
# Singleton reference
#################################################


singletons = Singletons()
