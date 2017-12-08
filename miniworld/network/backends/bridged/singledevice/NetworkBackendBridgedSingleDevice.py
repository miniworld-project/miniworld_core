from ordered_set import OrderedSet

from miniworld.model.connections.Connections import Connections
from miniworld.network.connection import AbstractConnection
from miniworld.network.backends import InterfaceFilter
from miniworld.network.backends.bridged.NetworkBackendBridged import NetworkBackendBridgedDummy
from miniworld.service.network.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.singletons import singletons
from miniworld.util import PathUtil


def NetworkBackendBridgedSingleDevice():
    # TODO: Ticket #84 make usable with all execution modes!
    class NetworkBackendBridgedSingleDevice(NetworkBackendBridgedDummy()):
        """

        Do not set default FORWARD policy to DROP, because ebtables should have no effect on the management network.
        All other connections are redirected to another chain.

        Attributes
        ----------
        bridges : dict<str, AbstractSwitch>
            Stores for each bridge name the according class.
        """

        ebtables_history_path = PathUtil.get_log_file_path("ebtables_history.txt")

        PREFIXES = ["ebtables"]

        # ShellCommandSerializer stuff
        # NOTE: due to same namespace, we must take core of not overriding the super event names as they are still used
        EBTABLES_EVENT_ROOT = "ebtables"
        EVENT_EBTABLES_CREATE_CHAINS = "ebtables_create_chain"
        EVENT_EBTABLES_REDIRECT = "ebtables_redirect"
        EVENT_EBTABLES_INIT = "ebtables_init"
        EVENT_EBTABLES_INIT_COMMIT = "ebtables_init_commit"
        EVENT_EBTABLES_UPDATE = "ebtables_update"
        EVENT_EBTABLES_COMMANDS = "ebtables_commands"
        EVENT_EBTABLES_FINISH = "ebtables_finish"
        EBTABLES_EVENT_ORDER = OrderedSet(
            [EVENT_EBTABLES_INIT, EVENT_EBTABLES_INIT_COMMIT, EVENT_EBTABLES_UPDATE, EVENT_EBTABLES_CREATE_CHAINS, EVENT_EBTABLES_REDIRECT, EVENT_EBTABLES_COMMANDS,
             EVENT_EBTABLES_FINISH])

        # TODO: DOC
        mark_cnt = 0

        def get_interface_filter(self):
            return InterfaceFilter.EqualInterfaceNumbers

        def get_network_provisioner(self):
            return NetworkConfiguratorSameSubnet

        @staticmethod
        def add_shell_ebtables_command(event, cmd):
            singletons.network_backend.shell_command_executor.add_command(
                NetworkBackendBridgedSingleDevice.EBTABLES_EVENT_ROOT, event,
                NetworkBackendBridgedSingleDevice.__class__.__name__, cmd, NetworkBackendBridgedSingleDevice.PREFIXES)

        def setup_shell_command_executor(self, shell_command_executor):

            shell_command_executor.add_group(self.EBTABLES_EVENT_ROOT)
            shell_command_executor.set_event_order(self.EBTABLES_EVENT_ROOT, self.EBTABLES_EVENT_ORDER)

        def __init__(self, *args, **kwargs):
            super(NetworkBackendBridgedSingleDevice, self).__init__(*args, **kwargs)
            self.bridges = {}

        def run_shell(self, cmd):
            return singletons.shell_helper.run_shell("network_backend", cmd, prefixes=["ebtables"])

        def reset(self):
            super(NetworkBackendBridgedSingleDevice, self).reset()

            self.init_ebtables()

        def before_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
            """
            Add atomic commit command for ebtables network change.

            Parameters
            ----------
            simulation_manager
            step_cnt
            network_backend
            emulation_nodes
            """

            conn_service = self.network_backend_bootstrapper.connection_service
            # TODO: MOVE method here ...
            if singletons.scenario_config.is_network_backend_bridged_execution_mode_batch():
                self.add_shell_ebtables_command(self.EVENT_EBTABLES_UPDATE, conn_service.ebtable_cmd_atomic_save)

            if step_cnt == 0:
                self.init_ebtables()

        def init_ebtables(self):
            # TODO: call from ShellCommandRunner
            conn_service = self.network_backend_bootstrapper.connection_service

            # reset to initial ebtables state
            self.add_shell_ebtables_command(self.EVENT_EBTABLES_INIT, conn_service.ebtable_cmd_atomic_init)
            self.add_shell_ebtables_command(self.EVENT_EBTABLES_INIT_COMMIT, conn_service.ebtable_cmd_atomic_commit)

        def get_br_name(self, number):
            return 'wifi%d' % number

        def get_bridge(self, interface):
            return self.bridges[self.get_br_name(interface.nr_host_interface)]

        def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x,
                                      interface_y, connection_info,
                                      start_activated=False, **kwargs):

            super(NetworkBackendBridgedSingleDevice, self).before_link_initial_start(network_backend, emulation_node_x,
                                                                                     emulation_node_y, interface_x,
                                                                                     interface_y, connection_info,
                                                                                     start_activated=staticmethod,
                                                                                     **kwargs)
            # start a single bridge here and add all tap devices to it
            # afterwards use ebtables for connection filtering on layer 2
            connection_type = self.network_backend_bootstrapper.connection_type
            connection_service = self.network_backend_bootstrapper.connection_service

            # TODO: DOC
            br_name = self.get_br_name(interface_x.nr_host_interface)
            if not self.bridges.get(br_name, None):
                self._logger.info("creating bridge %s", br_name)
                bridge = self.bridges[br_name] = self.network_backend_bootstrapper.switch_type(br_name, interface_x)
                # create extra chain for bridge
                self.add_shell_ebtables_command(self.EVENT_EBTABLES_CREATE_CHAINS,
                                                connection_service.get_ebtables_chain_cmd(br_name,
                                                                                          connection_service.policy_drop))
                # redirect to new chain
                self.add_shell_ebtables_command(self.EVENT_EBTABLES_REDIRECT,
                                                connection_service.get_ebtables_redirect_cmd(br_name))

                bridge.start(switch=False, bridge_dev_name=br_name)
            else:
                bridge = self.get_bridge(interface_x)

            connection = connection_type.from_connection_info(emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)
            connection_service.start(connection=connection)

            # TODO: #84: improve
            connections = Connections([(emulation_node_x, interface_x), (emulation_node_y, interface_y)])

            is_one_tap_mode = connection_info.is_one_tap_mode
            if not is_one_tap_mode:
                tap_x = self.get_tap_name(emulation_node_x._id, interface_x)
                tap_y = self.get_tap_name(emulation_node_y._id, interface_y)

                # TODO: #84: check which devices are already added to the bridge ...
                # add devices to bridge
                bridge.add_if(tap_x, if_up=True)
                bridge.add_if(tap_y, if_up=True)

            # TODO: nearly same code as in NetworkBackendBridgedMultiDevice!
            else:
                virtual_node, _if = None, None
                if connection_info.connection_type == AbstractConnection.ConnectionType.central:
                    virtual_node, _if = connections.filter_central_nodes()[0]
                elif connection_info.connection_type == AbstractConnection.ConnectionType.mgmt:
                    virtual_node, _if = connections.filter_mgmt_nodes()[0]

                tap_dev_name = None
                if connection_info.is_remote_conn:

                    tunnel_dev_name = self.get_tunnel_name(emulation_node_x._id, emulation_node_y._id)
                    # add the tunnel to the bridge
                    bridge.add_if(tunnel_dev_name, if_up=True)
                    remote_node, if_remote_node, local_emu_node, if_local_emu_node = singletons.simulation_manager._get_remote_node(
                        emulation_node_x, emulation_node_y, interface_x, interface_y)
                    # the tap device we want to add to the bridge is the local one, not the remote one!
                    tap_dev_name = self.get_tap_name(local_emu_node._id, if_local_emu_node)
                else:
                    emu_node, emu_if = connections.filter_real_emulation_nodes()[0]
                    tap_dev_name = self.get_tap_name(emu_node._id, emu_if)
                    bridge = virtual_node.switch

                # add the tap device to the bridge
                bridge.add_if(tap_dev_name, if_up=True)

            return True, bridge, connection

        def do_network_topology_change(self):
            """
            Run ebtable commands for batch or one shell call mode
            """
            is_pyroute2 = singletons.scenario_config.is_network_backend_bridged_execution_mode_pyroute2()
            is_batch = singletons.scenario_config.is_network_backend_bridged_execution_mode_batch()
            if is_batch:
                # add atomic commit command for ebtables network change
                conn_service = self.network_backend_bootstrapper.connection_service
                self.add_shell_ebtables_command(self.EVENT_EBTABLES_FINISH, conn_service.ebtable_cmd_atomic_commit)

                # ebtables_cmds = self.shell_command_executor.get_serialized_commands_event_order(self.EBTABLES_EVENT_ROOT)
                #
                # if singletons.scenario_config.is_network_backend_bridged_execution_mode_one_shell_call():
                #     # variant #1
                #     # TODO: cnt =1
                #     # TODO: DOCU
                #     # cmd = "sh -c '%s'" % ';\n'.join(ebtables_cmds)
                #     # # TODO: place node_id other than 0!
                #     # self.run_shell(cmd)
                #
                #     # variant #2: os.system
                #     # import os
                #     # for cmd in ebtables_cmds:
                #     #     os.system(cmd)
                #
                #     # variant #3: subprocess.check_output
                #     from miniworld.management import ShellHelper as sh
                #     for cmd in ebtables_cmds:
                #         sh.run_shell(cmd)
                #

                if singletons.scenario_config.is_network_backend_bridged_execution_mode_batch():
                    self.shell_command_executor.run_commands(events_order=self.EBTABLES_EVENT_ROOT)

            # may be already executed by batch
            if not is_batch and is_pyroute2:
                self.shell_command_executor.run_commands(events_order=self.EBTABLES_EVENT_ROOT)

    return NetworkBackendBridgedSingleDevice
