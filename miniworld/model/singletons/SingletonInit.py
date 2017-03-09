import miniworld.model.events.MyEventSystem
from miniworld import log
from miniworld.management import SimulationManager, NodeDistributionStrategy
from miniworld.model.spatial import Singleton
from miniworld.rpc import Protocol


def init_singletons():
    log.info("initializing singletons ...")
    from miniworld.management import ShellHelper
    from miniworld.management.network.manager import NetworkManager
    from miniworld.model.singletons.Singletons import singletons
    from miniworld.errors import SimulationErrors
    from miniworld.management import SimulationStateGarbageCollector
    from miniworld.model.emulation.Qemu import QemuProcessSingletons

    # create singletons here
    singletons.network_manager = NetworkManager.NetworkManager()
    singletons.shell_helper = ShellHelper.ShellHelper()
    singletons.spatial_singleton = Singleton.Singleton()
    singletons.event_system = miniworld.model.events.MyEventSystem.MyEventSystem()
    singletons.simulation_errors = SimulationErrors.SimulationErrors()
    singletons.simulation_state_gc = SimulationStateGarbageCollector.SimulationStateGarbageCollector()
    singletons.protocol = Protocol.factory()()
    singletons.node_distribution_strategy = NodeDistributionStrategy.factory()()

    singletons.simulation_manager = SimulationManager.factory()()
    singletons.qemu_process_singletons = QemuProcessSingletons()

    # they share state which needs to be cleared for a new simulation
    for singleton_with_simulation_scenario_state in [singletons.network_manager, singletons.shell_helper, singletons.spatial_singleton, singletons.simulation_errors]:
        singletons.simulation_state_gc.add_singleton_with_simulation_scenario_state_(singleton_with_simulation_scenario_state)