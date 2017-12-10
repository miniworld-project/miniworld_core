import functools
import hashlib
import json
import math
from collections import defaultdict
from copy import deepcopy
from io import StringIO
from pprint import pformat
from typing import Dict, Union

from ordered_set import OrderedSet

from miniworld.errors import Base, SimulationStateStartFailed
from miniworld.impairment import ImpairmentModel
from miniworld.impairment import LinkQualityConstants
from miniworld.mobility import DistanceMatrix
from miniworld.mobility.MovementDirectorFactory import MovementDirectorFactory
from miniworld.model import Lock
from miniworld.model.ResetableInterface import ResetableInterface
from miniworld.model.domain.interface import Interface
from miniworld.network.backends import NetworkBackends
from miniworld.network.backends.NetworkBackendNotifications import ConnectionInfo
from miniworld.network.connection import AbstractConnection
from miniworld.nodes.EmulationNodes import EmulationNodes
from miniworld.nodes.virtual.CentralNode import CentralNode
from miniworld.service.emulation import NodeStarter
from miniworld.service.emulation.RunLoop import RunLoop
from miniworld.service.event.MyEventSystem import MyEventSystem
from miniworld.service.persistence.connections import ConnectionPersistenceService
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.singletons import singletons
from miniworld.util import PathUtil, ConcurrencyUtil

__author__ = 'Nils Schmidt'


def factory():
    if singletons.config.is_mode_distributed():
        if singletons.config.is_coordinator():
            return SimulationManagerDistributedCoordinator
        else:
            return SimulationManagerDistributedClient

    return EmulationManager


class EmulationManager(ResetableInterface):
    """
    This class is responsible for managing the simulation.
    The simulation can run assisted or automatically (a :py:class:`RunLoop` triggers every time step the step() method).
    In the first case some external program has to call it.

    The step() method asks the :py:class:`MovementDirector` for the current distance matrix.
    According to a :py:class:`.LinkQualityModel` the link quality is adjusted.

    Attributes
    ----------
    running : bool
    auto_stepping : bool
    run_loop : RunLoop

    nodes_id_mapping : dict<int, EmulationNode>
        Maps the ID to a node
    central_nodes : dict<int, CentralNode>
        Maps the ID to a node

    network_backend : NetworkBackend

    current_step : int, default is 1
        Current step count
    link_quality_model : ImpairmentModel
        The model which describes the change of link quality in the event of distance matrix change.
    movement_director: MovementDirector

    distance_matrix : dict< (int, int), int)
    distance_matrix_hubwifi : dict< (int, int), int)
    """

    class Error(Base):
        pass

    class NoMovementDirector(Error):
        pass

    def __init__(self):
        self.path_log_file = PathUtil.get_log_file_path(self.__class__.__name__)
        self._logger = singletons.logger_factory.get_logger(self)
        self._logger.info("starting ...")
        self._connection_persistence_service = ConnectionPersistenceService()

        # NOTE: init resets first for reset()
        self.reset()
        self.reset_scenario_changed()

    ###############################################
    # Resetable
    ###############################################

    def reset(self):
        self.run_loop = None
        self.scenario_changed = False
        self.auto_stepping = None
        self.running = False

        self.current_step = 0

        # no director means no run-loop
        self.movement_director = None
        self.impairment = None
        self.distance_matrix = DistanceMatrix.factory()()
        self.distance_matrix_hubwifi = DistanceMatrix.factory()()

        self.network_backend = None

    def reset_scenario_changed(self):
        self.nodes_id_mapping = {}
        self.central_nodes_id_mapping = {}

    ###############################################
    # Getter
    ###############################################

    def _is_auto_stepping_and_running(self):
        return self.running and self.auto_stepping

    def is_movement_director_enabled(self):
        return self.movement_director is not None or singletons.config.is_mode_distributed()

    def get_emulation_nodes(self):
        """
        Get all :py:class:`.EmulationNode` from the current simulation.

        Returns
        -------
        EmulationNodes
        """
        return EmulationNodes(OrderedSet(self.nodes_id_mapping.values())).filter_real_emulation_nodes()

    def get_emulation_node_ids(self):
        """
        Returns
        -------
        list<int>
        """
        # filter out virtual nodes!
        return [node._node._id for node in self.get_emulation_nodes()]

    ###############################################
    # CentralHub
    ###############################################

    def pre_calculate_hubwifi_distance_matrix(self, nodes) -> DistanceMatrix:
        """
        Precalculate the distance matrix where each node with a :py:class:`.HubWiFi` interface is connected
        to the `CentralHub`.
        """
        if self.distance_matrix_hubwifi:
            return self.distance_matrix_hubwifi

        matrix = {}
        cnt_nodes = len(nodes)
        self._logger.info("cnt_nodes: %d", cnt_nodes)
        cnt_central_nodes = len(self.central_nodes_id_mapping)
        if cnt_central_nodes > 0:
            self._logger.info("cnt_central_nodes: %d", cnt_central_nodes)
            # NOTE: we need a float division here for the case that we have more CentralNodes than nodes
            nodes_stepping = cnt_nodes * 1.0 / cnt_central_nodes
            self._logger.info("nodes_stepping: %d", nodes_stepping)
            for idx, node in enumerate(nodes):
                node_id = node._id
                self._logger.info("loop: %s, %s, %s", idx, node_id, node)

                if idx == 0:
                    idx_central_node = 0
                else:
                    idx_central_node = int(math.ceil(idx / nodes_stepping)) - 1
                self._logger.info("idx_central_node: %s", idx_central_node)
                bridge_node_id = list(self.central_nodes_id_mapping.keys())[idx_central_node]

                if [interface for interface in node._node.interfaces if interface.name == Interface.InterfaceType.hub.value]:
                    # NOTE: we keep the upper triangular matrix
                    matrix[(node_id, bridge_node_id)] = ImpairmentModel.VAL_DISTANCE_ZERO
                else:
                    matrix[(node_id, bridge_node_id)] = ImpairmentModel.VAL_DISTANCE_UNLIMITED

            self.distance_matrix_hubwifi = DistanceMatrix.factory()(matrix)
            return self.distance_matrix_hubwifi

    ###############################################
    # RunLoop stuff
    ###############################################

    def start_run_loop(self):
        """
        Note
        ----
        Not thread-safe!
        """
        self.run_loop = RunLoop(self)
        self.run_loop.daemon = True
        self.run_loop.start()
        self._logger.info("starting %s", self.run_loop)

        return self.run_loop

    def stop_run_loop(self):
        """
        Stop the run loop and wait until the thread terminated.
        """
        self.run_loop.terminate()
        self.run_loop.join()
        self.run_loop = None

    def raise_run_loop_exception(self):
        """
        Check if an exception occurred in the :py:class:`RunLoop`.
        If yes, raise the exception.

        Returns
        -------
        False

        Raises
        ------
        Exception
        """

        if hasattr(self.run_loop, 'raise_objects'):
            # no exception
            if self.run_loop.raise_objects is None:
                return False

            # exception
            raise_objects = self.run_loop.raise_objects
            self.abort()

            raise raise_objects[0]

        # no run-loop yet
        return False

    ###############################################
    # Simulation management
    ###############################################

    @staticmethod
    def _get_scenario_hash():
        if singletons.scenario_config is not None:
            scenario_config = singletons.scenario_config.data
        # may not be set yet
        else:
            scenario_config = {}

        config_json = json.dumps(scenario_config, sort_keys=True)
        hasher = hashlib.sha256()
        hasher.update(config_json.encode())
        return hasher.hexdigest()

    def start(self, scenario_config: Dict, auto_stepping=False, force_snapshot_boot=False):
        """
        Parse the scenario config and run the simulation.

        Parameters
        ----------
        scenario_config
            Scenario config file (json).
        auto_stepping
        blocking : bool, optional (default is True)
        force_snapshot_boot: bool, optional (default is False)
            Disable snapshoot boot scenario comparison check and force snapshot boot

        Raises
        ------
        SimulationStateStartFailed
        """
        try:

            # force snapshot boot
            if force_snapshot_boot:
                self.scenario_changed = False
            else:
                # calculate old and new hash of scenario_config and check if scenario changed
                old_scenario_digest = self._get_scenario_hash()

            # store scenario file globally
            singletons.scenario_config.data = scenario_config

            if not force_snapshot_boot:
                # first set new scenario config
                new_scenario_digest = self._get_scenario_hash()
                self.scenario_changed = old_scenario_digest != new_scenario_digest
                if self.scenario_changed:
                    self.reset_scenario_changed()

            # no shapshot boot, clear database
            if self.scenario_changed:
                singletons.db_session.clear_state()
            else:
                self._connection_persistence_service.delete()

            self._logger.info('setting scenario config')

            # init EventSystem after scenario config is set
            event_system = singletons.event_system

            # the following events have to be considered for the autostepping mode
            if auto_stepping:
                event_system.events.extend(
                    [MyEventSystem.EVENT_NETWORK_BACKEND_SETUP, MyEventSystem.EVENT_VM_SHELL_POST_NETWORK_COMMANDS])

            self._logger.info("responsible for nodes: %s",
                              ','.join(map(str, singletons.scenario_config.get_local_node_ids())))

            return self._start(auto_stepping=auto_stepping)

        except Exception as e:
            self._logger.critical("Encountered an error while starting the simulation! You should reset the system (mwcli stop)!")
            self._logger.exception(e)
            # self.abort()
            raise SimulationStateStartFailed("Failed to start the simulation!") from e

    def _start(self, auto_stepping=None):
        """
        Start the simulation (thread-safe)

        This includes the following steps:
        1. Create the network backend
        2. Start it
        3. Start the nodes
        4. Create the :py:class:`.CentralNode s and connect them to the nodes
        5. Add 0 distance to the distance matrix for the :py:class:`.HubWifi` links
        6. Create the :py:class:`.MovementDirector`
        7. Start the :py:class:`.RunLoop` if necessary and wait until the network has been setup

        Parameters
        ----------
        node_ids : list<int>, optional (default is all node ids)

        Returns
        -------
        list<EmulationNode>
        """

        # get scenario settings
        cnt_nodes = int(singletons.scenario_config.get_number_of_nodes())
        interfaces = singletons.scenario_config.get_interfaces()
        path_qemu_image = singletons.scenario_config.get_path_image()
        post_boot_script_string_io = StringIO(singletons.scenario_config.get_all_shell_commands_pre_network_start())
        network_backend_name = singletons.scenario_config.get_network_backend()
        node_ids = singletons.scenario_config.get_local_node_ids()
        # supply the LinkQualityModel the default link settings
        kwargs = dict(bandwidth=singletons.scenario_config.get_link_bandwidth(),
                      loss=LinkQualityConstants.LINK_QUALITY_VAL_LOSS_NONE)
        self._logger.info("using interface link quality: %s", pformat(kwargs))
        # load LinkQualityModel
        link_quality_model = ImpairmentModel.ImpairmentModel.import_link_quality_model(
            singletons.scenario_config.get_link_quality_model())(**kwargs)

        with singletons.lock_manager.lock(resource=Lock.Resource.emulation, type=Lock.Type.write):

            if node_ids is None:
                node_ids = range(0, cnt_nodes)

            self.impairment = link_quality_model

            # create and start network backend
            network_backend_bootstrapper = singletons.network_backend_bootstrapper_factory.get()
            singletons.network_backend_bootstrapper = network_backend_bootstrapper
            self._logger.info("creating network backend ...")
            self.network_backend = network_backend_bootstrapper.network_backend_type(network_backend_bootstrapper)
            # store singleton reference to network backend
            singletons.network_backend = self.network_backend

            # NOTE: required for init_for_next_scenario
            self.auto_stepping = auto_stepping

            # init e.g. network configurators
            # NOTE: set network backend before!
            singletons.network_manager.init_for_next_scenario()

            self._logger.info("starting network backend ...")
            self.network_backend.start()

            # start nodes
            node_starter = NodeStarter.NodeStarter(node_ids, network_backend_name)
            emulation_nodes, _ = node_starter.start_nodes(path_qemu_image, post_boot_script_string_io,
                                                          interfaces=interfaces,
                                                          )

            # NOTE: first the EmulationNodes then the CentralHubs need to be created
            self.central_nodes_id_mapping = self.network_backend.create_n_connect_central_nodes()
            self.pre_calculate_hubwifi_distance_matrix(emulation_nodes)

            node_persistence_service = NodePersistenceService()
            for central_node in self.central_nodes_id_mapping.values():
                node_persistence_service.add(central_node)

            self._logger.debug("nodes: %s", pformat(self.nodes_id_mapping))
            self._logger.info("topology mode : '%s'", singletons.scenario_config.get_walk_model_name())

            if not singletons.config.is_mode_distributed():
                self.movement_director = MovementDirectorFactory().get(cnt_nodes)
                self._logger.info("%s running ... ", self.movement_director)

            if singletons.config.is_qemu_snapshot_boot():
                self.create_snapshots_parallel()

        if self.auto_stepping:
            self.try_start_run_loop(auto_stepping)

        self.running = True
        return emulation_nodes

    def exec_node_cmd(self, cmd, node_id=None, validation=True, timeout=None) -> Union[str, Dict[int, str]]:
        """
        Execute a command on a node or all nodes.

        Parameters
        ----------
        node_id
        cmd
        validation
        timeout
        """
        nodes = self.get_emulation_nodes()

        def get_fun(node):
            fun = node.virtualization_layer.run_commands_eager_check_ret_val if validation else node.virtualization_layer.run_commands_eager
            return functools.partial(fun, timeout=timeout)

        if node_id is None:
            jobs = {}
            res = {}
            with ConcurrencyUtil.node_start_parallel() as executor:
                for node in nodes:
                    fun = get_fun(node)
                    jobs[node._id] = executor.submit(fun, StringIO(cmd))

                for node_id, job in jobs.items():
                    res[node_id] = job.result()

            return res

        else:
            fun = get_fun(self.nodes_id_mapping[node_id])

            return fun(StringIO(cmd))

    def try_start_run_loop(self, auto_stepping):
        # we need the run-loop only with a `MovementDirector`
        if self.is_movement_director_enabled():
            self.auto_stepping = auto_stepping

            if self.auto_stepping:
                self.start_run_loop()

    def abort(self):
        # with mylock(self.lock):
        if self._is_auto_stepping_and_running():
            self._logger.info("%s aborted ... ", self)
            # TODO: REMOVE
            self._logger.info("stop_run_loop() ...")
            self.stop_run_loop()
            self._logger.info("stop_run_loop() [done]")

        singletons.simulation_state_gc.reset_simulation_scenario_state()
        self.reset()

    def pause(self):
        raise NotImplementedError

    def resume(self):
        raise NotImplementedError

    def is_connection_among_servers(self, emulation_node_x, emulation_node_y):
        return False

    ###############################################
    # Helpers
    ###############################################

    def set_hubwifi_on_connection_info(self, interface: Interface, connection_info: ConnectionInfo) -> bool:
        # HubWiFi interface: do not change connections, but apply link quality
        is_hubwifi_iface = interface.name == Interface.InterfaceType.hub
        if is_hubwifi_iface:
            connection_info.connection_type = AbstractConnection.ConnectionType.central

        return is_hubwifi_iface

    # TODO:
    @staticmethod
    def get_central_node(emulation_node_x, emulation_node_y, interface_x, interface_y):
        """

        Parameters
        ----------
        emulation_nodes
        interfaces

        Returns
        -------
        CentralNode, HubWifi, EmulationNode, Interface
            central_node, if_hubwifi, emu_node, if_emu_node
        """
        return (emulation_node_x, interface_x, emulation_node_y, interface_y) if CentralNode.is_central_node(
            emulation_node_x) else (emulation_node_y, interface_y, emulation_node_x, emulation_node_x)

    def get_distance_matrix_diff(self, new_distance_matrix):
        """
        This method is not idempotent.

        Parameters
        ----------
        new_distance_matrix

        Returns
        -------
        DistanceMatrix
        """

        # TODO: #52: maybe numpy is faster for comparing matrices
        # do not take the distance matrix for the CentralHub into account (doesn't change)

    ###############################################
    # Simulation stepping
    ###############################################

    def step(self, steps, distance_matrix=None):
        """
        This method is responsible for tracking the changes in the network topology
        which are signaled by the :py:class:`.MovementDirector` by a distance matrix.
        According to the distance, a :py:class:`.LinkQualityModel` determines the link quality.

        If the distance matrix did not change between steps or no `py:class:`.MovementDirector` exists,
        no actions are done at all.

        The distance matrix gets updated with the distances for the :py:class:`.CentralHub`.
        Each node which has a :py:class:`.HubWiFi` interface, has no distance to the :py:class:`.CentralHub`.
        This modified distance matrix is stored in the :py:class:`.NetworkManager` singleton.

        The unmodified distance matrix is stored in this class,
        so that we can check the matrix for changes.

        Parameters
        ----------
        steps : int
            The number of steps to step.
        distance_matrix

        Returns
        -------
        dict<int, DistanceMatrix>

        Raises
        ------
        ValueError
            If the distance matrix is None
        """

        def _step(distance_matrix):

            if self.is_movement_director_enabled():

                if not distance_matrix:
                    self.movement_director.simulate_one_step()
                    # TODO: #52: avoid big matrices
                    distance_matrix = self.movement_director.get_distances_from_nodes()

                if distance_matrix is None:
                    raise ValueError("The supplied distance matrix is invalid: '%s", distance_matrix)

                singletons.network_manager.before_simulation_step(self, self.current_step, self.network_backend,
                                                                  self.get_emulation_nodes())

                distance_matrix_diff = self.distance_matrix.diff(distance_matrix)
                self.distance_matrix = distance_matrix_diff

                # only call the following methods for changes in distance matrix
                if self.current_step == 0 or distance_matrix_diff:

                    self._logger.info("change in distance matrix ...")

                    # add distances to CentralHub
                    distance_matrix_diff.update(self.distance_matrix_hubwifi)
                    distance_matrix.update(self.distance_matrix_hubwifi)

                    # NOTE: take distances for CentralHub into account
                    singletons.network_manager.before_distance_matrix_changed(self, self.network_backend,
                                                                              distance_matrix_diff,
                                                                              distance_matrix)

                    # only look at changes in distance matrix
                    for (x, y), distance in distance_matrix_diff.items():
                        # assume upper triangular matrix
                        # of course do not connected to itself!
                        if x < y:
                            self._step_inner((x, y), distance)

                    self._logger.info("stepping %d", steps)
                    singletons.network_manager.after_distance_matrix_changed(self, self.network_backend,
                                                                             distance_matrix_diff,
                                                                             distance_matrix)

                    # TODO: choose correct network backend
                    singletons.network_manager.after_simulation_step(self, self.current_step, self.network_backend,
                                                                     self.get_emulation_nodes())
                self.after_network_setup_done()
                self.current_step += 1

                return distance_matrix_diff

            else:
                raise self.NoMovementDirector()

        with singletons.lock_manager.lock(resource=Lock.Resource.emulation, type=Lock.Type.write):

            for _ in range(steps):
                _step(distance_matrix)

    # TODO: DOC
    def after_network_setup_done(self):
        # network setup done
        if self.current_step == 0:
            # call run_post_network_shell_commands for each EmulationNode
            # for emulation_node in self.get_emulation_nodes():
            #     emulation_node.run_post_network_shell_commands()

            with ConcurrencyUtil.network_provision_parallel() as executor:
                res = executor.map(lambda node: node.run_post_network_shell_commands(), self.get_emulation_nodes())
                # wait for evaluation!
                list(res)

    def create_snapshots_parallel(self):
        self._logger.info("creating snapshots ...")
        with ConcurrencyUtil.node_start_parallel() as executor:
            res = executor.map(lambda node: node.virtualization_layer.make_snapshot(), self.get_emulation_nodes())
            # wait for evaluation!
            list(res)

    def get_emulation_node_for_idx(self, idx):
        return self.nodes_id_mapping[idx]

    def _step_inner(self, node_ids, distance):
        """
        Do a step but only if the node_ids are according to an upper triangular matrix.

        Parameters
        ----------
        node_ids: (int, int)
        distance: int
        """
        x, y = node_ids

        connection_info = ConnectionInfo()
        connection_info.step_added = self.current_step
        connection_info.distance = distance

        link_quality_model_says_connected, link_quality_dict = self.impairment.distance_2_link_quality(distance)
        self._logger.debug("LinkQuality for %s,%s: %s", x, y, pformat(link_quality_dict))

        node_x, node_y = self.get_emulation_node_for_idx(x), self.get_emulation_node_for_idx(y)

        # no connect yet and shall not be connected -> ignore
        # NOTE: for connected nodes which shall be disconnected we cannot simply break here -> existing connections must be closed
        if not link_quality_model_says_connected and not self._connection_persistence_service.exists(node_x_id=x, node_y_id=y):
            self._logger.debug("ignoring %s,%s: %s", x, y, pformat(link_quality_dict))
            return

        # TODO: this method belongs to the distributed simulationmanager!

        if self.is_connection_among_servers(node_x, node_y):

            server_to_ip_mapping = singletons.scenario_config.get_network_backend_bridged_tunnel_endpoints()
            # get the ip addresses for the tunnels
            # TODO: REMOVE
            try:
                ip_x, ip_y = server_to_ip_mapping[self.get_server_for_node(node_x.id)], server_to_ip_mapping[
                    self.get_server_for_node(node_y.id)]
                remote_ip = None

                if self.is_local_node(x):
                    remote_ip = ip_y
                else:
                    remote_ip = ip_x

                # TODO: add interface and connection info
                singletons.network_manager.connection_across_servers(self.network_backend, node_x, node_y, remote_ip)
                connection_info.is_remote_conn = True
            except KeyError:
                self._logger.critical(pformat(singletons.scenario_config.get_distributed_server_node_mapping()))

        self._logger.debug("processing %s: %s", x, y)
        # TODO: ensure upper triangular matrix!
        # set connections where the LinkQualityModel says the nodes are connected
        # + apply the initial link quality settings

        self._step_no_connection_yet(link_quality_model_says_connected, link_quality_dict, distance, node_x, node_y,
                                     connection_info)
        self._step_connection(link_quality_model_says_connected, link_quality_dict, node_x, node_y, connection_info)

    def _step_no_connection_yet(self, link_quality_model_says_connected, link_quality_dict, distance, emulation_node_x,
                                emulation_node_y, connection_info):
        """
        Connect all interfaces according to the decision of the :py:class:`.LinkQualityModel`
          except the :py:class:`.Management` and :py:class:`.HubWiFi`.
        Afterwards adjust the link quality.

        1. Check if a :py:class:`.AbstractConnection` exists for (x, y).
        2. Run over all equal interfaces types of both nodes except the :py:class:`.Management` interface.
        3. Ask the :py:class:`.LinkQualityModel` for the initial link quality
            + for link quality with distance taken into account
            + if the nodes are connected at all
            The link quality settings with distance have higher priority.
        4. Only proceed if the "normal" nodes are connected (:py:class:`.LinkQualityModel` decision)
        5. For all interfaces except :py:class:`.HubWiFi` place a AbstractConnection between them with 100% loss.
           The :py:class:`.HubWiFi` interfaces are already connected!
        6. Adjust the link quality for the interfaces.

        Parameters
        ----------
        link_quality_model_says_connected : bool
        link_quality_dict
        distance : int
        node_id_x : int
        emulation_node_x : EmulationNode
        node_id_y : int
        emulation_node_y: EmulationNode
        connection_info : ConnectionInfo
        """

        # TODO: put into connection_info
        is_exactly_one_central_node = len(list(
            filter(lambda x: x is True, (
                CentralNode.is_central_node(emulation_node_x), CentralNode.is_central_node(emulation_node_y))))) == 1

        # only connect equal interfaces
        # for management interface: do not connect nodes with each other and do not apply link quality adjustments!
        # TODO: speed improvement!
        interface_filter = self.network_backend.get_interface_filter()()

        # use filter so that the NetworkBackend can decide which interfaces shall be connected
        for interface_x, interface_y in interface_filter.get_interfaces(emulation_node_x, emulation_node_y):

            # TODO: improvement #1: store mgmt iface in extra variable
            # TODO: improvement #2: store hubwifi iface in extra variable
            # TODO: improvement #3: own method for central node connection management -> iterate over nodes and connect central node interface
            if interface_x.name == interface_y.name and not interface_x.name == Interface.InterfaceType.management:

                # does a connection already exists? (active or inactive)
                if not self._connection_persistence_service.exists(node_x_id=emulation_node_x._node._id, node_y_id=emulation_node_y._node._id,
                                                                   interface_x_id=interface_x._id, interface_y_id=interface_y._id):
                    # no connection exists

                    # HubWiFi interface: do not change connections, but apply link quality
                    # TODO: put into connection_info
                    is_hubwifi_iface = self.set_hubwifi_on_connection_info(interface_x, connection_info)

                    connection = None
                    if not is_hubwifi_iface:
                        # only meaningful for non HubWifi links
                        if link_quality_model_says_connected:

                            self._logger.debug("connecting %s@%s <-> %s@%s (connection is not yet up!)",
                                               emulation_node_x, interface_x, emulation_node_y, interface_y)

                            # NetworkBackendNotifications
                            connected, switch, connection = singletons.network_manager.before_link_initial_start(
                                self.network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                connection_info,
                                start_activated=False)
                            singletons.network_manager.after_link_initial_start(connected, switch, connection,
                                                                                self.network_backend,
                                                                                emulation_node_x, emulation_node_y,
                                                                                interface_x, interface_y,
                                                                                connection_info,
                                                                                start_activated=False)

                            if connected:
                                # NOTE: first create the connection in before_link_initial_start
                                singletons.network_manager.link_up(connection, link_quality_dict, self.network_backend,
                                                                   emulation_node_x, emulation_node_y, interface_x,
                                                                   interface_y, connection_info)
                    else:
                        # find the bridge node
                        if is_exactly_one_central_node:
                            bridge_node, emu_node = (emulation_node_x, emulation_node_y) if CentralNode.is_central_node(
                                emulation_node_x) else (emulation_node_y, emulation_node_x)
                            switch, connection, interface_x, interface_y = bridge_node.connect_to_emu_node(
                                self.network_backend, emu_node)

    # TODO: DOC link_quality_dict
    def _step_connection(self, link_quality_model_says_connected, link_quality_dict, emulation_node_x, emulation_node_y,
                         connection_info):
        """
        Adjust the link quality for already connected nodes
        there a :py:class:`.AbstractConnection` already exists.

        Parameters
        ----------
        link_quality_model_says_connected : bool
        link_quality_dict
        emulation_node_x : EmulationNode
        emulation_node_y: EmulationNode
        connection_info : ConnectionInfo
        """

        def call_link_quality_adjustment_notifications(connection, link_quality_dict, interface_x, interface_y):
            # no step done yet -> new connection -> set initial link quality, used e.g. to set the initial bandwidth
            if self.current_step == 0:
                _, link_quality_dict_initial = self.impairment.get_initial_link_quality()

                # take the initial link quality settings such as 54Mbit/s bandwidth
                # then take the distance into account and update the settings
                link_quality_dict_initial.update(link_quality_dict)

                link_quality_dict = link_quality_dict_initial

            # NetworkBackendNotifications
            singletons.network_manager.before_link_quality_adjustment(
                connection, link_quality_model_says_connected, link_quality_dict, self.network_backend,
                emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)
            singletons.network_manager.after_link_quality_adjustment(
                connection, link_quality_model_says_connected, link_quality_dict, self.network_backend,
                emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)

        for connection in self._connection_persistence_service.all(
                node_x_id=emulation_node_x._node._id,
                node_y_id=emulation_node_y._node._id,
                connected=True,
                connection_type=AbstractConnection.ConnectionType.user,
        ):  # type: List[AbstractConnection]
            interface_x, interface_y = connection.interface_x, connection.interface_y

            if link_quality_model_says_connected:
                call_link_quality_adjustment_notifications(connection, link_quality_dict, interface_x, interface_y)
            else:
                # active connection moved to inactive
                singletons.network_manager.link_down(connection, link_quality_dict, self.network_backend,
                                                     emulation_node_x, emulation_node_y, interface_x, interface_y,
                                                     connection_info)

        if link_quality_model_says_connected:
            # inactive connection moved to active
            for connection in self._connection_persistence_service.all(
                    node_x_id=emulation_node_x._node._id,
                    node_y_id=emulation_node_y._node._id,
                    connected=False,
                    connection_type=AbstractConnection.ConnectionType.user,
            ):  # type: List[AbstractConnection]
                interface_x, interface_y = connection.interface_x, connection.interface_y

                call_link_quality_adjustment_notifications(connection, link_quality_dict, interface_x, interface_y)

                singletons.network_manager.link_up(connection, link_quality_dict, self.network_backend,
                                                   emulation_node_x, emulation_node_y, interface_x, interface_y,
                                                   connection_info)

    def get_server_for_node(self, node_id):
        return 1


# TODO: merge back in normal SimulationManager ?


class DistributedModeSimulationManager(EmulationManager):
    """

    Attributes
    ----------
    server_node_mapping : dict<int, list<int>>
        Stores for each emulation server the list of nodes it maintains.
    all_nodes_id_mapping : dict<int, EmulationNode>
        All nodes that take part in the distributed simulation.
    """

    def reset(self):
        super(DistributedModeSimulationManager, self).reset()
        self._all_nodes_id_mapping = {}

    def get_server_for_node(self, node_id):
        for server, nodes in singletons.scenario_config.get_distributed_server_node_mapping().items():
            if node_id in nodes:
                return server

    def get_emulation_node_for_idx(self, idx):
        try:
            return self.nodes_id_mapping[idx]
        except KeyError:
            return self.all_nodes_id_mapping[idx]

    @property
    def all_nodes_id_mapping(self):
        if not self._all_nodes_id_mapping:
            emu_node_type = NetworkBackends.get_current_network_backend_bootstrapper().emulation_node_type
            self._all_nodes_id_mapping = {_id: emu_node_type.factory(_id) for _id in
                                          range(1, singletons.scenario_config.get_number_of_nodes() + 1)}
        return self._all_nodes_id_mapping

    # TODO: REMOVE ?
    def map_distance_matrix_to_servers(self, distance_matrix):
        """
        We do not need the whole distance matrix for each server.
        Only entries, where a distance to a node which the server maintains is listed, is necessary.
        This function filters these entries for each server.

        Parameters
        ----------
        distance_matrix

        Returns
        -------
        dict< int, dict<(int, int>, int> >>
            Distance matrix for each server
        """
        res = defaultdict(dict)

        if not singletons.config.is_publish_individual_distance_matrices():
            for server_id in singletons.scenario_config.get_distributed_server_ids():
                res[server_id] = distance_matrix
            return res
        else:
            # create a dict for each server
            for server_id in singletons.scenario_config.get_distributed_server_ids():
                res[server_id]

            for (x, y), distance in distance_matrix.items():
                res[self.get_server_for_node(x)][(x, y)] = distance
                res[self.get_server_for_node(y)][(x, y)] = distance

            return res


class SimulationManagerDistributedClient(DistributedModeSimulationManager):
    def is_local_node(self, emulation_node_id):
        return emulation_node_id in self.get_local_node_ids()

    def is_connection_among_servers(self, emulation_node_x, emulation_node_y):
        """
        Check if we need a tunnel between the two nodes.

        Returns
        -------
        bool
        """

        # TODO: #90
        if not EmulationNodes((emulation_node_x, emulation_node_x)).filter_real_emulation_nodes():
            return False

        # an node
        local_1 = self.is_local_node(emulation_node_x._node._id)
        local_2 = self.is_local_node(emulation_node_y._node._id)
        if local_1 != local_2:
            return True
        return False

    def get_local_node_ids(self):
        """
        Get the node_ids for which this server is responsible (distributed mode)

        Returns
        -------
        list<int>
        """
        return list(self.nodes_id_mapping.keys())

    def get_local_distance_matrix_to_servers(self, whole_distance_matrix):
        """
        We do not need the whole distance matrix for each server.
        Only entries, where a distance to a node which the server maintains is listed, is necessary.
        This function filters these entries for each server.

        Parameters
        ----------
        whole_distance_matrix

        Returns
        -------
        dict<(int, int>, int>>
            Distance matrix for this erver
        """
        res = {}
        local_node_ids = self.get_local_node_ids()
        for (x, y), distance in whole_distance_matrix.items():
            if x in local_node_ids or y in local_node_ids:
                res[(x, y)] = distance
                res[(x, y)] = distance

        return DistanceMatrix.factory()(res)

    def get_remote_node(self, emulation_node_x, emulation_node_y, interface_x, interface_y):
        """

        Parameters
        ----------
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y

        Returns
        -------
        EmulationNode, Interface, EmulationNode, Interface
            remote_node, if_remote_node, local_emu_node, if_local_emu_node
        """
        return (emulation_node_x, interface_x, emulation_node_y, interface_y) if not self.is_local_node(
            emulation_node_x._node._id) else (emulation_node_y, interface_y, emulation_node_x, interface_x)


class SimulationManagerDistributedCoordinator(DistributedModeSimulationManager):
    def _start(self, scenario_name, cnt_nodes, path_qemu_image, post_boot_script_string_io, interfaces,
               link_quality_model, network_backend_name,
               parallel=True, auto_stepping=False,
               node_ids=None):

        with singletons.lock_manager.lock(resource=Lock.Resource.emulation, type=Lock.Type.write):
            self.movement_director = MovementDirectorFactory.factory(cnt_nodes)
            self.impairment = link_quality_model

        singletons.zeromq_server.wait_for_scenario_config.set()

        singletons.zeromq_server.wait_for_nodes_started.wait()
        # TODO: doc wait for zeromq start
        with singletons.lock_manager.lock(resource=Lock.Resource.emulation, type=Lock.Type.write):
            # NOTE: the RunLoop is started after the scenario config has been set from the zeromq server
            # (needed for the distance matrix distribution)
            self.try_start_run_loop(auto_stepping)
            self.running = True
            self._logger.info("%s running ... ", self)

    @staticmethod
    def create_scenario_configs(server_node_mapping):
        """

        Parameters
        ----------
        server_node_mapping

        Returns
        -------
        dict<int, dict>
            Dict of the scenario configs.
        """
        scenario_configs = {}
        for server in server_node_mapping:
            singletons.scenario_config.set_distributed_server_id(server)
            scenario_config = deepcopy(singletons.scenario_config.data)
            scenario_configs[server] = scenario_config
        return scenario_configs

    # TODO: DOC
    def transform_distance_matrix(self, distance_matrix):
        """

        Parameters
        ----------
        distance_matrix

        Returns
        -------
        dict<(int, int), int> or dict<int, dict<(int, int), int>
            The first is the normal distance matrix. The latter for each node the local distance matrix.
        """
        if singletons.config.is_protocol_zeromq_mode_mcast():
            return distance_matrix
        else:
            return self.map_distance_matrix_to_servers(distance_matrix)

    # TODO: abstract more with super step?
    def step(self, steps, distance_matrix=None):
        """
        This method is responsible for tracking the changes in the network topology
        which are signaled by the :py:class:`.MovementDirector` by a distance matrix.
        According to the distance, a :py:class:`.LinkQualityModel` determines the link quality.

        If the distance matrix did not change between steps or no :py:class:`.MovementDirector` exists,
        no actions are done at all.

        The distance matrix gets updated with the distances for the :py:class:`.CentralHub`.
        Each node which has a :py:class:`.HubWiFi` interface, has no distance to the :py:class:`.CentralHub`.
        This modified distance matrix is stored in the :py:class:`.NetworkManager` singleton.

        The unmodified distance matrix is stored in this class,
        so that we can check the matrix for changes.

        Parameters
        ----------
        steps : int
            The number of steps to step.
        distance_matrix

        Raises
        ------
        ValueError
            If the distance matrix is None

        Returns
        -------
        DistanceMatrix
        """

        # TODO:
        if steps > 1:
            self._logger.critical("Not more than one step supported in the distributed mode! Doing only one step!")

        with singletons.lock_manager.lock(resource=Lock.Resource.emulation, type=Lock.Type.write):
            if self.is_movement_director_enabled():

                if not distance_matrix:
                    self.movement_director.simulate_one_step()
                    # TODO: #52: avoid big matrices
                    distance_matrix = self.movement_director.get_distances_from_nodes()
                    distance_matrix = self.transform_distance_matrix(distance_matrix)

                if distance_matrix is None:
                    raise ValueError("The supplied distance matrix is invalid: '%s", distance_matrix)

                self._logger.info("waiting for zeromq server to handle the distance_matrix ...")

                if singletons.config.is_publish_only_new_distance_matrices():
                    pass

                # TODO: implement difference checking
                singletons.zeromq_server.handle_state_distance_matrix(distance_matrix)
                self.current_step += 1

                return distance_matrix

    def get_emulation_node_ids(self):
        """
        Returns
        -------
        list<int>
        """
        return singletons.scenario_config.get_all_emulation_node_ids()
