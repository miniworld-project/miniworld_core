from collections import defaultdict, OrderedDict
from pprint import pformat

from dictdiffer import DictDiffer

from miniworld import singletons
from miniworld.Scenario import scenario_config
from miniworld.log import log
from miniworld.management.network.manager.provisioner.NetworkConfiguratorP2P import NetworkConfiguratorP2P
from miniworld.management.network.manager.provisioner.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.model.emulation.nodes.EmulationNodes import EmulationNodes
from miniworld.model.emulation.nodes.virtual.ManagementNode import ManagementNode
from miniworld.model.events.MyEventSystem import MyEventSystem
from miniworld.model.network.backends import NetworkBackendNotifications
from miniworld.model.network.connections.ConnectionStore import ConnectionStore
from miniworld.model.network.interface.Interface import Management
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import *
from miniworld.model.singletons.Resetable import Resetable
from miniworld.util import PlotUtil, PathUtil

PATH_LOG_FILE_NETWORK_CHECK_COMMANDS = PathUtil.get_log_file_path("network_check_commands.txt")

NETWORK_CONFIGURATOR_NAME_SAME_SUBNET = 'same_subnet'
NETWORK_CONFIGURATOR_NAME_P2P = 'p2p'

__author__ = 'Nils Schmidt'

KEY_DISTANCE = "distance"

# TODO: MOVE CONNECTIONS HERE ...
# TODO: STORE EMUNODES OR NODE IDS?
# TODO: move link_quality stuff to connections
class NetworkManager(Resetable, NetworkBackendNotifications.NetworkBackendNotifications):
    '''
    Keeps track of the network connections.
    For this purpose, it receives events from the :py:class:`.SimulationManager`,
    defined by the :py:class:`.NetworkBackendNotifications` interface.

    This class allows every :py:class:`.NetworkBackend` to transparently use the benefits
    of this class:

    Attributes
    -------
    connection_store : miniworld.management.network.manager.ConnectionStore.ConnectionStore
    cnt_nodes  : int

    step_cnt : int
    new_conns_per_node : dict<int, set<int>>
        The new connections each node has.
        Calculated for each change in the distance matrix.
        Fully qualified matrix.
    distance_matrix : dict<(int, int), int>
    '''

    def __init__(self):
        self.reset()

    def init_for_next_scenario(self):
        '''
        Call first if the scenario config is set.
        '''
        self.reset()
        self.net_configurator = self.get_network_provisioner()

        event_system = singletons.event_system
        if singletons.simulation_manager.auto_stepping:
            if scenario_config.is_network_links_auto_ipv4() and self.net_configurator:
                log.info("adding network setup to EventSystem ...")
                event_system.events.append(MyEventSystem.EVENT_NETWORK_SETUP)
                if scenario_config.is_connectivity_check_enabled():
                    log.info("adding network check to EventSystem ...")
                    event_system.events.append(MyEventSystem.EVENT_NETWORK_CHECK)

        event_system.ready.set()
        log.info("%s ready ... ", event_system.__class__.__name__)

        if self.net_configurator:
            self.net_configurator = self.net_configurator(singletons.network_backend.get_interface_index)

    def get_network_provisioner(self):
        '''

        Returns
        -------
        type
            Subclass of NetworkConfigurator
        '''

        if singletons.network_backend.get_network_provisioner():
            return singletons.network_backend.get_network_provisioner()

        if scenario_config.get_network_provisioner_name() == NETWORK_CONFIGURATOR_NAME_P2P:
            return NetworkConfiguratorP2P
        elif scenario_config.get_network_provisioner_name() == NETWORK_CONFIGURATOR_NAME_SAME_SUBNET:
            return NetworkConfiguratorSameSubnet


    def ip_config(self):
        # NOTE: we need to reuse the existing configurators due to their internal state!
        if scenario_config.is_network_links_auto_ipv4():
            log.info("using ip provisioner: %s" % scenario_config.get_network_provisioner_name())

            new_connections = self.get_new_connections_with_interfaces_since_last_distance_matrix_change()
            with open(PathUtil.get_log_file_path("%s.txt" % self.__class__.__name__), "a") as f:

                if self.net_configurator.needs_reconfiguration(singletons.simulation_manager.current_step):

                    # only connection setup and check for new connections
                    log.info("%s: configuring network ...", self.net_configurator.__class__.__name__)
                    commands_per_node = self.net_configurator.get_nic_configuration_commands(new_connections)
                    self.net_configurator.apply_nic_configuration_commands(commands_per_node)

                    f.write("setup_commands: %s\n" % pformat(dict(commands_per_node)))

                    # # TODO: disable for distributed mode?
                    # # # perform full topology check
                    # if scenario_config.is_connectivity_check_enabled():
                    #     log.info("checking connectivity ...")
                    #     check_commands_per_node = self.net_configurator.get_nic_check_commands(new_connections)
                    #     f.write("check_commands: %s\n" % pformat(dict(check_commands_per_node)))
                    #
                    #     self.net_configurator.apply_nic_configuration_commands(check_commands_per_node)

    #########################################
    ### Resettable Interface
    #########################################

    def reset(self):
        self.connection_store = ConnectionStore()
        self.cnt_nodes = 0

        self.step_cnt = 0
        self.new_conns_per_node = {}
        self.distance_matrix = {}

    #########################################
    ### Bandwidth
    #########################################

    @property
    def bandwidth(self):
        return self.connection_store.get_active_node_connection_store().get_link_quality_matrix(
            include_interfaces=False, key=LINK_QUALITY_KEY_BANDWIDTH)

    def bandwidth_matrix(self):
        return self._to_matrix(self.bandwidth)

    #########################################
    ### Distance
    #########################################

    @property
    def distance(self):
        return self.distance_matrix

    def distance_matrix(self):
        return self._to_matrix(self.distance)

    #########################################
    ### Loss
    #########################################

    @property
    def loss(self):
        return self.connection_store.get_link_quality_matrix(
            include_interfaces=False, key=LINK_QUALITY_KEY_LOSS)

    # TODO: use decorator to offer loss_matrix and to_matrix method
    def loss_matrix(self):
        return self._to_matrix(self.loss)

    def _to_matrix(self, matrix, fill_in="-"):
        return PlotUtil.fill_quadratic_matrix(matrix, size=self.cnt_nodes, fill_in=fill_in)

    #############################################################
    ### NetworkBackendNotifications
    ### Propagate notifications to :py:class:`.NetworkBackend`
    ### and return the result.
    #############################################################

    def before_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        '''
        Remember the current step cnt.
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        '''
        self.step_cnt = step_cnt
        return network_backend.before_simulation_step(simulation_manager, step_cnt, network_backend, emulation_nodes)

    def after_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        '''
        For the new connections which have been created in this step, perform some network checks ( if enabled ).
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        '''

        if scenario_config.is_network_links_auto_ipv4() and scenario_config.is_connectivity_check_enabled():
            new_connections = self.get_new_connections_with_interfaces_since_last_distance_matrix_change()
            with open(PATH_LOG_FILE_NETWORK_CHECK_COMMANDS, "a") as f:
                # perform full topology check
                log.info("checking connectivity ...")
                check_commands_per_node = self.net_configurator.get_nic_check_commands(new_connections)
                f.write("check_commands: %s\n" % pformat(dict(check_commands_per_node)))

                self.net_configurator.apply_nic_check_commands(check_commands_per_node)

        self.net_configurator.reset()
        return network_backend.after_simulation_step(simulation_manager, step_cnt, network_backend, emulation_nodes)

    def before_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                       full_distance_matrix, **kwargs):
        '''
        Remember the active interfaces per node. This is needed for the :py:meth:`.get_new_connections`.
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        '''
        self.distance_matrix = full_distance_matrix

        es = singletons.event_system
        
        # clear progress for network backend setup
        with es.event_init(es.EVENT_NETWORK_BACKEND_SETUP, finish_ids=[]) as ev:
            pass

        # fully qualified matrix
        # dict<int, set<int>>
        conns_per_node = defaultdict(set)

        # check for new connections whether they are connected
        for (x, y), distance in full_distance_matrix.items():
            connected, _ = simulation_manager.link_quality_model.distance_2_link_quality(distance)
            if connected:
                conns_per_node[x].add(y)
                conns_per_node[y].add(x)

        all_node_ids = conns_per_node.keys() + self.new_conns_per_node.keys()
        self.new_conns_per_node = {
                    node_id: (conns_per_node.get(node_id, set()) - self.new_conns_per_node.get(node_id, set())) for node_id in
            all_node_ids}

        # keep the old distance matrix
        self.distance_matrix = full_distance_matrix


        self.active_interfaces_per_connection_before_distance_matrix_changed = singletons.network_manager.connection_store.get_active_interfaces_per_connection()

        return network_backend.before_distance_matrix_changed(simulation_manager, network_backend,
                                                              changed_distance_matrix, full_distance_matrix)

    def after_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                      full_distance_matrix, **kwargs):

        # first let the NetworkBackend handle
        res = network_backend.after_distance_matrix_changed(simulation_manager, network_backend,
                                                            changed_distance_matrix, full_distance_matrix)

        self.ip_config()
        return res


    def get_new_connections_with_interfaces_since_last_distance_matrix_change(self):
        ''' Get only new connections since distance matrix changed.

        Returns
        -------
        OrderedDict<EmulationNodes, tuple<Interfaces>>>
        '''
        active_connections = singletons.network_manager.connection_store.get_active_interfaces_per_connection()

        # first step -> return all connections
        if singletons.simulation_manager.current_step == 0:
            return active_connections
        # return only the diff
        else:
            # NOTE: we only have a look at the new connections, not changed ones etc.
            dd = DictDiffer(active_connections,
                            self.active_interfaces_per_connection_before_distance_matrix_changed)

            return OrderedDict([(k, active_connections[k]) for k in dd.added()])

    # TODO: {before,after}_link_stop ?
    def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                  start_activated=False, **kwargs):
        return network_backend.before_link_initial_start(network_backend, emulation_node_x, emulation_node_y,
                                                         interface_x, interface_y, connection_info, start_activated=start_activated)

    def after_link_initial_start(self, network_backend_connected, switch, connection, network_backend, emulation_node_x,
                                 emulation_node_y, interface_x, interface_y, connection_info, start_activated=False, **kwargs):
        # try:
        #     type_check(network_backend_connected, bool)
        #     type_check(switch, AbstractSwitch.AbstractSwitch)
        #     type_check(connection, AbstractConnection.AbstractConnection)
        # except ValueError:
        #     print "foo"
            
        es = singletons.event_system

        if network_backend_connected:
            self.connection_store.add_connection(emulation_node_x, emulation_node_y, interface_x, interface_y, connection,
                                            network_backend_connected)

            # TODO: enable again!
            # TODO: management nodes
            # both real EmulationNode s
            # if len(EmulationNodes([emulation_node_x, emulation_node_y]).filter_real_emulation_nodes()) == 2:
            #     # notify EventSystem about the network setup of both nodes
            #     # TOdO: #84: fix
            #     with es.event_no_init_finish(es.EVENT_NETWORK_BACKEND_SETUP) as ev:
            #         cnt_normal_ifaces_x = len(emulation_node_x.network_mixin.interfaces.filter_normal_interfaces())
            #         cnt_normal_ifaces_y = len(emulation_node_y.network_mixin.interfaces.filter_normal_interfaces())
            #         ev.update([emulation_node_x.id], 1.0 / ( len(self.new_conns_per_node[emulation_node_x.id]) * cnt_normal_ifaces_x), add=True)
            #         ev.update([emulation_node_y.id], 1.0 / ( len(self.new_conns_per_node[emulation_node_y.id]) * cnt_normal_ifaces_y), add=True)

        return network_backend.after_link_initial_start(network_backend_connected, switch, connection, network_backend,
                                                        emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                                        start_activated=start_activated)

    def before_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                       network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                       **kwargs):
        return network_backend.before_link_quality_adjustment(
            connection, link_quality_still_connected, link_quality_dict, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)

    def after_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                      network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                      **kwargs):

        self.connection_store.update_link_quality(emulation_node_x, emulation_node_y, interface_x, interface_y,
                                                  connection, link_quality_still_connected, link_quality_dict)
        return network_backend.after_link_quality_adjustment(
            connection, link_quality_still_connected, link_quality_dict, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)


    def link_up(self, connection, link_quality_dict,
                    network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                    **kwargs):
        # flag as active/inactive connection
        self.connection_store.change_connection_state(emulation_node_x, emulation_node_y, interface_x, interface_y, now_active=True)
        res = network_backend.link_up(
            connection, link_quality_dict,
            network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
            **kwargs)
        return res


    def link_down(self, connection, link_quality_dict,
                  network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                  **kwargs):
        # flag as active/inactive connection
        self.connection_store.change_connection_state(emulation_node_x, emulation_node_y, interface_x, interface_y, now_active=False)
        res = network_backend.link_down(
            connection, link_quality_dict,
            network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
            **kwargs)
        return res

    def connection_across_servers(self, network_backend, emulation_node_x, emulation_node_y, remote_ip):

        tunnel = network_backend.connection_across_servers(network_backend, emulation_node_x, emulation_node_y, remote_ip)
        return tunnel

    #########################################
    ### Helpers
    #########################################

    # TODO: DOC
    # TODO: REMOVE
    def to_id_matrix(self, d):
        '''

        Parameters
        ----------
        d: dict<(EmulationNode,EmulationNode), object>

        Returns
        -------
        d: dict<str, object>
        '''
        return {(emu_node_x.id, emu_node_y.id): item for (emu_node_x, emu_node_y), item in d.items()}

    # TODO: #15: cleanup
    # TODO: REMOVE
    @staticmethod
    def transform_distance_matrix(distance_matrix, ids):
        '''

        Parameters
        ----------
        distance_matrix : dict( (int, int), object >
        ids

        Returns
        -------

        '''

        from collections import defaultdict

        distance_matrix_by_node = defaultdict(list)

        for (x, y), val in sorted(distance_matrix.items()):
            distance_matrix_by_node[x].append(val)

        # TODO: OPTIMIZE
        distance_matrix_by_node = [
            [""] * (len(ids) - len(distance_matrix_by_node[node_id])) + distance_matrix_by_node[node_id] for node_id in
            ids]
        return distance_matrix_by_node

    # TODO:
    def create_vde_switch_topology(self, include_management_node=False, include_nodes=True):
        '''

        Parameters
        ----------
        include_management_node : bool, optional (default is False)
            Include the management switch and it's connections in the topology
        include_nodes : : bool, optional (default is False)
            Include the nodes and connect them with their interfaces. Otherwise show interfaces only!

        Returns
        -------

        '''

        group_node = 1
        group_interface = 2

        def get_interface_name(emu_node, interface):
            return "%s_%s" % (emu_node.id, interface.node_class_name)

        def get_node_name(emu_node):
            return emu_node.id

        def get_interface_group(interface):
            return group_interface + interface.node_class

        import networkx as nx
        from networkx.readwrite import json_graph

        G = nx.Graph()

        # TODO: #54,#55
        for (emu_node_x, emu_node_y), nic_connection_store in self.connection_store.get_active_node_connection_store().items():
            emu_node_x_str = get_node_name(emu_node_x)
            emu_node_y_str = get_node_name(emu_node_y)
            connections = nic_connection_store.keys()

            # add nodes
            if not include_management_node and (
                isinstance(emu_node_x, ManagementNode) or isinstance(emu_node_y, ManagementNode)):
                continue

            if include_nodes:
                G.add_node(emu_node_x_str, group=group_node, name=emu_node_x_str)
                G.add_node(emu_node_y_str, group=group_node, name=emu_node_y_str)

            for conn in connections:

                interface_x, interface_y = conn
                interface_x_str = get_interface_name(emu_node_x, interface_x)
                interface_y_str = get_interface_name(emu_node_y, interface_y)

                # add interfaces and connect them
                for emu_node, interface, interface_str in (
                (emu_node_x, interface_x, interface_x_str), (emu_node_y, interface_y, interface_y_str)):

                    # add interfaces
                    G.add_node(interface_str, group=get_interface_group(interface), name=interface_str)

                    # connect node to interface
                    if include_nodes:
                        G.add_edge(get_node_name(emu_node), interface_str, group=get_interface_group(interface))

                # connect interfaces
                G.add_edge(interface_x_str, interface_y_str, group=get_interface_group(interface_x))

        d = json_graph.node_link_data(G)

        # log.info("topology: %s", pformat(G.edges()))
        return d

if __name__ == '__main__':
    from miniworld import testing

    testing.init_testing_environment()

    (n1, i1, conn), (n2, i2, _), conn_store = list(testing.get_pairwise_connected_nodes(2))

    x = conn_store.get_link_quality_matrix(include_interfaces=False, key='loss')
    print x

    # print conn_store.get_link_quality_matrix(False)
    #
    # conn_store.update_link_quality(n1, n2, i1, i2, conn, False, {})
    # print conn_store.get_link_quality_matrix(False)
    #
    # print conn_store.get_active_node_connection_store()
    # print conn_store.get_inactive_node_connection_store()
