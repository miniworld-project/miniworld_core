from pprint import pformat

from miniworld.model.ResetableInterface import ResetableInterface
from miniworld.network.backends import NetworkBackendNotifications
from miniworld.service.event.MyEventSystem import MyEventSystem
from miniworld.service.network.NetworkConfiguratorFactory import NetworkConfiguratorFactory
from miniworld.service.persistence.connections import ConnectionPersistenceService
from miniworld.singletons import singletons
from miniworld.util import PathUtil

PATH_LOG_FILE_NETWORK_CHECK_COMMANDS = PathUtil.get_log_file_path("network_check_commands.txt")

__author__ = 'Nils Schmidt'

KEY_DISTANCE = "distance"


class NetworkManager(ResetableInterface, NetworkBackendNotifications.NetworkBackendNotifications):
    """
    Keeps track of the network connections.
    For this purpose, it receives events from the :py:class:`.SimulationManager`,
    defined by the :py:class:`.NetworkBackendNotifications` interface.

    This class allows every :py:class:`.NetworkBackend` to transparently use the benefits
    of this class:

    Attributes
    -------
    step_cnt : int
    distance_matrix : dict<(int, int), int>
    """

    def __init__(self):
        self.reset()
        self._logger = singletons.logger_factory.get_logger(self)
        self.connection_persistence_service = ConnectionPersistenceService()

    def init_for_next_scenario(self):
        """
        Call first if the scenario config is set.
        """
        self.reset()

        self.net_configurator = NetworkConfiguratorFactory.get()

        event_system = singletons.event_system
        if singletons.simulation_manager.auto_stepping:
            if singletons.scenario_config.is_network_links_auto_ipv4() and self.net_configurator:
                self._logger.info("adding network setup to EventSystem ...")
                event_system.events.append(MyEventSystem.EVENT_NETWORK_SETUP)
                if singletons.scenario_config.is_connectivity_check_enabled():
                    self._logger.info("adding network check to EventSystem ...")
                    event_system.events.append(MyEventSystem.EVENT_NETWORK_CHECK)

        event_system.ready.set()
        self._logger.info("%s ready ... ", event_system.__class__.__name__)

        if self.net_configurator:
            self.net_configurator = self.net_configurator(singletons.network_backend.get_interface_index)

    def ip_config(self):
        # NOTE: we need to reuse the existing configurators due to their internal state!
        if singletons.scenario_config.is_network_links_auto_ipv4():
            self._logger.info("using ip provisioner: %s" % singletons.scenario_config.get_network_provisioner_name())

            with open(PathUtil.get_log_file_path("%s.txt" % self.__class__.__name__), "a") as f:

                if self.net_configurator.needs_reconfiguration(singletons.simulation_manager.current_step):
                    # only connection setup and check for new connections
                    self._logger.info("%s: configuring network ...", self.net_configurator.__class__.__name__)
                    commands_per_node = self.net_configurator.get_nic_configuration_commands()
                    self.net_configurator.apply_nic_configuration_commands(commands_per_node)

                    f.write("setup_commands: %s\n" % pformat(dict(commands_per_node)))

    #########################################
    # Resettable Interface
    #########################################

    def reset(self):
        self.net_configurator = None

        self.step_cnt = 0
        self.distance_matrix = {}

    #############################################################
    # NetworkBackendNotifications
    # Propagate notifications to :py:class:`.NetworkBackend`
    # and return the result.
    #############################################################

    def before_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        """
        Remember the current step cnt.
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        """
        self.step_cnt = step_cnt
        return network_backend.before_simulation_step(simulation_manager, step_cnt, network_backend, emulation_nodes)

    def after_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        """
        For the new connections which have been created in this step, perform some network checks ( if enabled ).
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        """

        if singletons.scenario_config.is_network_links_auto_ipv4() and singletons.scenario_config.is_connectivity_check_enabled():
            with open(PATH_LOG_FILE_NETWORK_CHECK_COMMANDS, "a") as f:
                # perform full topology check
                self._logger.info("checking connectivity ...")
                check_commands_per_node = self.net_configurator.get_nic_check_commands()
                f.write("check_commands: %s\n" % pformat(dict(check_commands_per_node)))

                self.net_configurator.apply_nic_check_commands(check_commands_per_node)

        self.net_configurator.reset()
        return network_backend.after_simulation_step(simulation_manager, step_cnt, network_backend, emulation_nodes)

    def before_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                       full_distance_matrix, **kwargs):
        """
        Remember the active interfaces per node. This is needed for the :py:meth:`.get_new_connections`.
        See :py:class:`NetworkBackendNotifications` for documentation on the arguments.
        """
        self.distance_matrix = full_distance_matrix

        es = singletons.event_system

        # clear progress for network backend setup
        with es.event_init(es.EVENT_NETWORK_BACKEND_SETUP, finish_ids=[]):
            pass

        # keep the old distance matrix
        self.distance_matrix = full_distance_matrix

        return network_backend.before_distance_matrix_changed(simulation_manager, network_backend,
                                                              changed_distance_matrix, full_distance_matrix)

    def after_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                      full_distance_matrix, **kwargs):

        # first let the NetworkBackend handle
        res = network_backend.after_distance_matrix_changed(simulation_manager, network_backend,
                                                            changed_distance_matrix, full_distance_matrix)

        self.ip_config()
        return res

    def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                  connection_info,
                                  start_activated=False, **kwargs):
        return network_backend.before_link_initial_start(network_backend, emulation_node_x, emulation_node_y,
                                                         interface_x, interface_y, connection_info,
                                                         start_activated=start_activated)

    def after_link_initial_start(self, network_backend_connected, switch, connection, network_backend, emulation_node_x,
                                 emulation_node_y, interface_x, interface_y, connection_info, start_activated=False,
                                 **kwargs):
        if network_backend_connected:
            connection.connected = True
            self.connection_persistence_service.add(connection)

        return network_backend.after_link_initial_start(network_backend_connected, switch, connection, network_backend,
                                                        emulation_node_x, emulation_node_y, interface_x, interface_y,
                                                        connection_info,
                                                        start_activated=start_activated)

    def before_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                       network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                       connection_info,
                                       **kwargs):
        return network_backend.before_link_quality_adjustment(
            connection, link_quality_still_connected, link_quality_dict, network_backend, emulation_node_x,
            emulation_node_y, interface_x, interface_y, connection_info)

    def after_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                      network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                      connection_info,
                                      **kwargs):

        connection.impairment = link_quality_dict
        self.connection_persistence_service.update_impairment(connection._id, link_quality_dict)
        self.connection_persistence_service.update_distance(connection._id, connection_info.distance)
        return network_backend.after_link_quality_adjustment(
            connection, link_quality_still_connected, link_quality_dict, network_backend, emulation_node_x,
            emulation_node_y, interface_x, interface_y, connection_info)

    def link_up(self, connection, link_quality_dict,
                network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                **kwargs):
        # flag as active/inactive connection
        self.connection_persistence_service.update_state(connection_id=connection._id, connected=True)

        res = network_backend.link_up(
            connection, link_quality_dict,
            network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
            **kwargs)
        return res

    def link_down(self, connection, link_quality_dict,
                  network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                  **kwargs):
        self.connection_persistence_service.update_state(connection_id=connection._id, connected=False)
        res = network_backend.link_down(
            connection, link_quality_dict,
            network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
            **kwargs)
        return res

    def connection_across_servers(self, network_backend, emulation_node_x, emulation_node_y, remote_ip):

        tunnel = network_backend.connection_across_servers(network_backend, emulation_node_x, emulation_node_y,
                                                           remote_ip)
        return tunnel
