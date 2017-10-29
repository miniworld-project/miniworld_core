import sys

from miniworld.network.backends.NetworkBackends import NetworkBackendBootstrapperFactory


def init_singletons():
    from miniworld.config.Scenario import ScenarioConfig
    from miniworld.service.LoggerFactory import LoggerFactory
    print("initializing singletons ...", file=sys.stderr)
    from miniworld.service.LockManager import LockManager
    import miniworld.service.event.MyEventSystem
    from miniworld.distributed import NodeDistributionStrategy
    from miniworld.mobility import Singleton
    from miniworld.mobility.Roads import Roads
    from miniworld.service.rpc import Protocol
    from miniworld.service.emulation import EmulationManager
    from miniworld.singletons.Singletons import singletons
    from miniworld.service.shell import shell
    from miniworld.service.network import NetworkManager
    from miniworld.model import SimulationErrors
    from miniworld.service import ScenarioGarbageCollector
    from miniworld.nodes.qemu.Qemu import QemuProcessSingletons
    from miniworld import Constants

    # create singletons here
    # other singletons may require a logger, hence create it first
    singletons.logger_factory = LoggerFactory()
    # default logger
    singletons.log = singletons.logger_factory.get_logger(Constants.PROJECT_NAME)
    singletons.lock_manager = LockManager()

    singletons.network_manager = NetworkManager.NetworkManager()
    singletons.shell_helper = shell.ShellHelper()
    singletons.spatial_singleton = Singleton.Singleton()
    singletons.spatial_singleton.roads = Roads()
    singletons.event_system = miniworld.service.event.MyEventSystem.MyEventSystem()
    singletons.simulation_errors = SimulationErrors.SimulationErrors()
    singletons.simulation_state_gc = ScenarioGarbageCollector.ScenarioGarbageCollector()
    singletons.protocol = Protocol.factory()()
    singletons.node_distribution_strategy = NodeDistributionStrategy.factory()()

    singletons.simulation_manager = EmulationManager.factory()()
    singletons.qemu_process_singletons = QemuProcessSingletons()
    singletons.scenario_config = ScenarioConfig()
    singletons.network_backend_bootstrapper_factory = NetworkBackendBootstrapperFactory()

    # they share state which needs to be cleared for a new simulation
    for singleton_with_simulation_scenario_state in [singletons.network_manager, singletons.shell_helper,
                                                     singletons.spatial_singleton, singletons.simulation_errors]:
        singletons.simulation_state_gc.add_singleton(
            singleton_with_simulation_scenario_state)
