from miniworld.network.backends.bridged.iproute2.NetworkBackendBridged import NetworkBackendBridgedIproute2
from miniworld.singletons import singletons


def NetworkBackendBridgedBrctl():
    class NetworkBackendBridgedBrctl(NetworkBackendBridgedIproute2()):
        """
        1. Use brctl to setup and config bridges
        2. Use iproute2 for the remaining stuff
        """

        def do_network_topology_change(self):
            # execute ip commands in batch mode, brctl in parallel
            # there is no batch mode for brctl
            if singletons.scenario_config.is_network_backend_bridged_execution_mode_batch():
                bridge_type = self.network_backend_bootstrapper.switch_type
                # execute all bridge stuff with brctl
                self.shell_command_executor.run_commands(
                    max_workers=singletons.scenario_config.get_network_backend_cnt_minions(),
                    events_order=bridge_type.EVENT_ROOT)

            super(NetworkBackendBridgedBrctl, self).do_network_topology_change()

    return NetworkBackendBridgedBrctl
