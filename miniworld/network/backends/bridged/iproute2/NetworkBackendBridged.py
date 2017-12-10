
from ordered_set import OrderedSet

from miniworld.network.backends.bridged import NetworkBackendBridged
from miniworld.network.backends.bridged.iproute2 import Constants
from miniworld.singletons import singletons


def NetworkBackendBridgedIproute2():
    class NetworkBackendBridgedIproute2(NetworkBackendBridged.NetworkBackendBridged()):
        """
        Use iproute2 to setup the network.
        """

        def __init__(self, network_backend_boot_strapper):
            super(NetworkBackendBridgedIproute2, self).__init__(network_backend_boot_strapper)
            self.myinit()

        def myinit(self):
            self.tunnels = {}

        def reset(self):
            self.myinit()
            super(NetworkBackendBridgedIproute2, self).reset()

        def setup_shell_command_executor(self, shell_command_executor):
            """
            Init the :py:class:`.ShellCommandExecutor` and set the command orders.
            Necessary to parallelize the command execution.
            """
            super(NetworkBackendBridgedIproute2, self).setup_shell_command_executor(shell_command_executor)

            bridge_type = self.network_backend_bootstrapper.switch_type
            conn_service = self.network_backend_bootstrapper.connection_service
            tunnel_type = self.network_backend_bootstrapper.tunnel_type
            EVENT_ORDER = [conn_service.EVENT_ROOT, tunnel_type.EVENT_ROOT, bridge_type.EVENT_ROOT]
            for elm in EVENT_ORDER:
                shell_command_executor.add_group(elm)

            shell_command_executor.set_event_order(bridge_type.EVENT_ROOT, bridge_type.EVENT_ORDER)
            shell_command_executor.set_event_order(conn_service.EVENT_ROOT, conn_service.EVENT_ORDER)
            shell_command_executor.set_event_order(tunnel_type.EVENT_ROOT, tunnel_type.EVENT_ORDER)

        def do_network_topology_change(self):

            super(NetworkBackendBridgedIproute2, self).do_network_topology_change()

            # run ip commands in batch mode
            if singletons.scenario_config.is_network_backend_bridged_execution_mode_batch():

                # TODO: solution implemented in shell_command_executor better than regex?!
                # shell shell_commands
                shell_commands = self.shell_command_executor.get_all_commands()
                # list->str
                shell_commands = '\n'.join(shell_commands)

                def execute_batch_iproute2_commands():
                    # remove all ip prefixes ("ip ")
                    # find ip shell_commands and strip "ip " prefix
                    # remove duplicates which may rise from multiple groups with OrderedSet()
                    ip_commands = '\n'.join(OrderedSet(NetworkBackendBridged.re_find_ip.findall(shell_commands)))

                    # NOTE: run shell_commands in batch mode, this is much faster than doing it sequentially
                    cmd = "ip -d -batch -"
                    self._logger.info("changing network topology with '%s'. See '%s' for the commands." % (
                        cmd, NetworkBackendBridged.PATH_SHELL_COMMANDS))
                    singletons.shell_helper.run_shell_with_input(cmd, ip_commands)

                # Use iproute2 only
                execute_batch_iproute2_commands()
            # execute all commands in non-batch parallel mode
            else:
                self.shell_command_executor.run_commands()

        def after_distance_matrix_changed(self, *args, **kwargs):
            """
            Log shell commands used to setup the network topology.
            """

            with open(NetworkBackendBridged.PATH_SHELL_COMMANDS, "a") as f:
                f.write(self.shell_command_executor.get_verbose_info())

            super(NetworkBackendBridgedIproute2, self).after_distance_matrix_changed(*args, **kwargs)

            # TODO: DOC return type!

        def connection_across_servers(self, network_backend, emulation_node_x, emulation_node_y, remote_ip):
            self._logger.info("connection_among_servers")

            # TODO: destroy tunnels again!
            tunnel_name = self.get_tunnel_name(emulation_node_x._node._id, emulation_node_y._node._id)
            # TODO:
            # new = False
            if tunnel_name not in self.tunnels:
                # new = True
                t = self.network_backend_bootstrapper.tunnel_type(emulation_node_x, emulation_node_y, remote_ip)
                # with open(PathUtil.get_log_file_path("d_debug.txt"), "aw") as f:
                #     f.write("%s, %s\n" % (tunnel_name, new))
                #     from pprint import pformat
                #     f.write("%s\n" % (pformat(self.tunnels)))
                #     f.write("\n")
                t.start()

                self.tunnels[tunnel_name] = t
            # else:
            #     # remove tunnel
            #     self.tunnels[tunnel_name].shutdown()

            return self.tunnels[tunnel_name]

        def get_tunnel_name(self, emulation_node_x_id, emulation_node_y_id):
            """
            Order of arguments does not matter!

            Parameters
            ----------
            emulation_node_x_id : int
            emulation_node_y_id: int

            Returns
            -------
            str
            """
            node_id_1, node_id_2 = sorted((emulation_node_x_id, emulation_node_y_id))

            def get_tunnel_name(prefix):
                return "{prefix}_{id_fmt}_{id_fmt}".format(prefix=prefix, id_fmt=Constants.NODE_ID_FMT) % (
                    node_id_1, node_id_2)

            # NOTE: we cannot choose the prefix longer due to the maximum device name length
            if singletons.scenario_config.is_network_backend_bridged_distributed_mode_vlan():
                return get_tunnel_name("vl")
            elif singletons.scenario_config.is_network_backend_bridged_distributed_mode_gretap():
                return get_tunnel_name("gr")
            elif singletons.scenario_config.is_network_backend_bridged_distributed_mode_vxlan():
                return get_tunnel_name("vx")

    return NetworkBackendBridgedIproute2
