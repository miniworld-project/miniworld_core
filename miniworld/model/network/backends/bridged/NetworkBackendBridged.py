import os
import re
from os.path import dirname
from subprocess import check_output

from ordered_set import OrderedSet
from collections import defaultdict

from miniworld.Scenario import scenario_config
from miniworld.log import log
from miniworld.management import ShellHelper
from miniworld.management.serialization.ShellCommandSerializer import ShellCommandSerializer
from miniworld.model.emulation.nodes.virtual.CentralNode import is_central_node_interface
from miniworld.model.network.backends import NetworkBackend
from miniworld.model.network.backends.bridged.ConnectionBookKeeper import ConnectionBookKeeper
from miniworld.model.network.backends.bridged.iproute2.Constants import NODE_ID_FMT
from miniworld.model.network.interface.Interface import HubWiFi
from miniworld.model.singletons.Resetable import Resetable
from miniworld.util import PathUtil

__author__ = 'Nils Schmidt'


class EventMonitor(Resetable):
    '''
    Monitors new bridge events.

    Cleared per simulation step


    Attributes
    ----------
    new_bridges : OrderedSet<str>
    '''

    def __init__(self):
        self.reset()

    def reset(self):
        self.new_bridges = OrderedSet()

    def add_new_bridge(self, br):
        self.new_bridges.add(br)

#############################################################
### Execution Modes
#############################################################


def get_superclass_dynamic():
    assert scenario_config.is_network_backend_bridged_connection_mode_set()

    from miniworld.model.network.backends.bridged.multidevice.NetworkBackendBridgedMultiDevice import \
        NetworkBackendBridgedMultiDevice
    from miniworld.model.network.backends.bridged.singledevice.NetworkBackendBridgedSingleDevice import \
        NetworkBackendBridgedSingleDevice

    return NetworkBackendBridgedSingleDevice() if scenario_config.is_network_backend_bridged_connection_mode_single() else NetworkBackendBridgedMultiDevice()

# NOTE: note matching against "'" and ";" is done for a execution mode (see :py:meth.`Scenario.is_network_backend_bridged_execution_mode_one_shell_call`)
re_find_ip = re.compile("^ip\s+(.*)", re.MULTILINE)

# regex to strip tc prefix
re_tc = re.compile("^tc\s+(.*)", re.MULTILINE)

# regex to strip ip prefix
PATH_SHELL_COMMANDS = PathUtil.get_log_file_path("network_backend_%s.txt" % "shell_commands")

def NetworkBackendBridgedDummy():
    class NetworkBackendBridgedDummy(NetworkBackend.NetworkBackend()):

        '''
        Implementation of a network backend which uses Linux Ethernet Bridiging.

        The backend supports 3 execution modes:
        1. iproute2
        2. pyroute
        3. brctl

        Each execution mode is implemented as a subclass.

        - bridge events
        - :py:class:`.ShellCommandExecutor`
        - bridge/tap device name assignment to a connection
        - linux queuing discipline (htb)

        Attributes
        ----------
        all_connections : dict<int, list<int>>
            All connections the nodes can have at any time in one of the scenarios.
        shell_command_executor : ShellCommandSerializer
        '''

        def _start(self, *args, **kwargs):
            self.reset()

        # TODO: add interface for ShellCommandExecutor stuff and mention in commment
        def init_shell_command_executor(self):
            '''
            Init the :py:class:`.ShellCommandExecutor` and set the command orders.
            Necessary to parallelize the tc command execution.
            By default only the :py:class:`.AbstractConnection` subclass is expected to have ShellCommandExecutor stuff.
            '''
            self.shell_command_executor = ShellCommandSerializer()

        def setup_shell_command_executor(self, shell_command_executor):
            '''

            Parameters
            ----------
            shell_command_executor : ShellCommandSerializer
            '''
            conn_type = self.network_backend_bootstrapper.connection_type
            EVENT_ORDER = [conn_type.EVENT_ROOT]
            shell_command_executor.set_group_order(EVENT_ORDER)
            shell_command_executor.set_event_order(conn_type.EVENT_ROOT, conn_type.EVENT_ORDER)

        def reset_shell_command_executor(self):
            self.init_shell_command_executor()
            self.setup_shell_command_executor(self.shell_command_executor)

        def _shutdown(self):

            # TODO: #55: DOC
            self._br_id_mapping = {}

            self._tap_id_mapping = {}
            self._current_tap_dev_nr = defaultdict(lambda : 1)

            self._current_br_dev_nr = defaultdict(lambda : 1)
            self.event_monitor = EventMonitor()

            self.reset_shell_command_executor()

            # reset
            self.connection_book_keeper = ConnectionBookKeeper()

            # TODO: delete tunnels!

        def reset_simulation_step(self):
            self.event_monitor.reset()
            self.reset_shell_command_executor()

        def reset(self):
            log.info("resetting %s", self.__class__.__name__)
            # NOTE: call shutdown to prevent multiple calling of method
            self._shutdown()

        ###########################################################
        ### Bridge/Tap device mapping
        ###########################################################

        def get_br_name(self, node_id, interface):
            '''
            Get the bridge name for the `node_id` and `interface`.

            Parameters
            ----------
            node_id : str
            interface : Interface

            Returns
            -------
            str
            '''
            return 'br_%s_{id_fmt}'.format(id_fmt =NODE_ID_FMT) % (node_id, self.get_id_br_postfix(node_id, interface))

        def get_id_br_postfix(self, node_id, interface):
            long_id = '%s_%s_%s' % (node_id, interface.node_class, interface.nr_host_interface)
            if long_id in self._br_id_mapping:
                return self._br_id_mapping[long_id]
            short_id = self._current_br_dev_nr[node_id]
            self._br_id_mapping[long_id] = short_id
            self._current_br_dev_nr[node_id] += 1
            return short_id

        def get_tap_name(self, node_id, interface):
            '''
            Get the tap name for the `node_id` and `interface`.

            Parameters
            ----------
            node_id : str
            interface : Interface

            Returns
            -------
            str
            '''
            node_id = int(node_id)
            return 'tap_{id_fmt}_%x'.format(id_fmt =NODE_ID_FMT) % (node_id, self.get_id_tap_postfix(node_id, interface))

        def get_id_tap_postfix(self, node_id, interface):
            # log.debug("get_id_tap_postfix interface: '%s'", repr(interface))
            long_id = '%s_{id_fmt}_{id_fmt}'.format(id_fmt =NODE_ID_FMT) % (node_id, interface.node_class, interface.nr_host_interface)
            short_id = self._current_tap_dev_nr[node_id]
            if long_id in self._tap_id_mapping:
                return self._tap_id_mapping[long_id]

            self._tap_id_mapping[long_id] = short_id
            self._current_tap_dev_nr[node_id] += 1
            # log.debug("tap_id_mapping: %s", pformat(self._tap_id_mapping))
            return short_id

        # TODO: use
        def get_tap_name_template(self, prefix):
            if prefix > 2:
                raise ValueError("Choose a shorter prefix!")

            return "{prefix}_{id_fmt}_{id_fmt}".format(prefix=prefix, id_fmt=NODE_ID_FMT)

        #############################################################
        ### NetworkBackendNotifications
        #############################################################

        # TODO: create abstract event system
        # TODO: add event system to every networkbackend
        def after_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
            '''
            Notify about events, if registered for events.
            '''
            # notify script about new events
            event_hook_script_path = scenario_config.get_network_backend_event_hook_script()
            if event_hook_script_path and os.path.exists(event_hook_script_path):
                bridge_list = ' '.join(self.event_monitor.new_bridges)
                log.info("notified event_hook_script: %s" % check_output([event_hook_script_path, bridge_list], cwd=dirname(event_hook_script_path)))

            self.reset_simulation_step()

        def after_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix, full_distance_matrix, **kwargs):
            '''
            Do the actual network topology change.
            '''

            # configure network
            super(NetworkBackendBridgedDummy, self).after_distance_matrix_changed(simulation_manager, network_backend, changed_distance_matrix, full_distance_matrix, **kwargs)

            # NOTE: we can configure the network first after the link quality has been adjusted
            # and therefore the links have been marked as active/inactive

            self.do_network_topology_change()
            self.do_queueing_discipline()
            self.shell_command_executor.reset()

        # TODO: let NetworkBackend call before_link_quality_adjustment, link_down, and link_up by default
        def before_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                           network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                           **kwargs):
            '''
            Adjust the link quality.
            '''
            if connection:
                connection.adjust_link_quality(link_quality_dict)

        def link_up(self, connection, link_quality_dict,
                    network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                    **kwargs):
            if connection:
                connection.link_up(link_quality_dict)


        def link_down(self, connection, link_quality_dict,
                      network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                      **kwargs):
            if connection:
                connection.link_down(link_quality_dict)
                # TODO:
                #if connection_info.is_remote_conn():
                #    run_shell("ip l del {}".format(self.get_tunnel_name(emulation_node_x.id, emulation_node_y.id)))

        #############################################################
        ### NIC configuration
        #############################################################

        def get_interface_index(self, emulation_node, interface):
            return self.get_id_tap_postfix(emulation_node.id, interface) - 1

        #############################################################
        ### Actual connection changing/qdisc
        #############################################################

        def do_network_topology_change(self):
            raise NotImplementedError

        def do_queueing_discipline(self):
            '''
            Execute the linux qdisc commands for traffic shaping etc.
            '''

            # for the other modes the class :py:class:`.ShellCommandSerializer` takes over
            if scenario_config.is_network_backend_bridged_execution_mode_batch():
                # shell shell_commands
                shell_commands = self.shell_command_executor.get_all_commands()
                # list->str
                shell_commands = '\n'.join(shell_commands)

                # strip "tc " prefix
                commands_tc = '\n'.join(re_tc.findall(shell_commands))
                # NOTE: run shell_commands in batch mode, this is much faster than doing it sequentially

                cmd = "tc -d -batch -"
                log.info("changing network topology with '%s'. See '%s' for the commands." % (cmd, PATH_SHELL_COMMANDS))
                ShellHelper.run_shell_with_input(cmd, commands_tc)

        #############################################################
        ### Bridge/Connection handling
        #############################################################

        def create_n_store_switch(self, emulation_node_x, emulation_node_y, interface_x):
            '''
            Create a switch and store a reference locally in `event_monitor`.
            There are at maximum 10^5 bridges supported!
            This is a limitation of the nic device length on linux and our naming schema!

            Parameters
            ----------
            emulation_node_x
            emulation_node_y
            interface_x

            Returns
            -------
            Bridge
            '''

            max_id = 10**5
            if emulation_node_x.id > max_id or emulation_node_y.id > max_id:
                raise ValueError("Only %d nodes supported!" % max_id)

            br_name = 'br_{id_fmt}_{id_fmt}'.format(id_fmt =NODE_ID_FMT) % (emulation_node_x.id, emulation_node_y.id)

            bridge = self.network_backend_bootstrapper.switch_type(br_name, interface_x)
            bridge.start(switch=False, bridge_dev_name=br_name)

            self.event_monitor.add_new_bridge(br_name)

            return bridge

        # TODO: #54, #55: MERGE WITH ...
        def create_n_connect_central_nodes(self, interfaces):
            '''

            Parameters
            ----------
            interfaces

            Returns
            -------
            dict<int, CentralNode>
            '''
            from miniworld.model.singletons.Singletons import singletons

            # create CentralNode s but only if there is a HubWiFi interface
            # TODO: REMOVE
            cnt = 0
            central_nodes_dict = {}

            # connect local devices
            for _if in filter(lambda x: is_central_node_interface(x), interfaces):
                if cnt == 1:
                    raise ValueError("Only one '%s' interface supported at the moment!" % HubWiFi)

                # TODO: REFACTOR!
                # TODO: #54: make amount of nodes configurable
                count_central_nodes = 1
                for i in range(0, count_central_nodes):
                    central_node = self.network_backend_bootstrapper.central_node_type(self.network_backend_bootstrapper, id = i+1)
                    #central_node.id = self.get_br_name(central_node.id, central_node.interface)
                    # TODO: #54 make configurable!
                    log.debug("creating CentralNode with id: %s", central_node.id)
                    central_node.start(switch=False, bridge_dev_name=central_node.id)
                    central_nodes_dict[central_node.id] = central_node

                    # remember new bridges
                    self.event_monitor.add_new_bridge(central_node.id)

                cnt += 1

            # connect via server boundaries (overlay)
            node_ids = singletons.simulation_manager.get_emulation_node_ids()
            for x, y in zip(node_ids, node_ids[1:]):

                emulation_node_x = singletons.simulation_manager.get_emulation_node_for_idx(x)
                emulation_node_y = singletons.simulation_manager.get_emulation_node_for_idx(y)
                log.info("connecting %s<->%s", emulation_node_x, emulation_node_y)
                self.connection_across_servers(self, emulation_node_x, emulation_node_y)


            return central_nodes_dict

    return NetworkBackendBridgedDummy

def NetworkBackendBridged():
    '''
    NOTE: We need to create the class dynamically, otherwise after a reset and change of the network backend (new scenario) the backend stays the same!
    Returns
    -------
    NetworkBackendBridged
    '''
    class NetworkBackendBridged(get_superclass_dynamic()):
        pass

    return NetworkBackendBridged


if __name__ == '__main__':
    from collections import defaultdict
    from pprint import pformat

    connections = {1: [2], 2: [3, 1], 3: [2]}
    print(pformat(configure_network(connections)))