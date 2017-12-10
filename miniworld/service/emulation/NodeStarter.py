from copy import deepcopy
from threading import Lock, Event

from sqlalchemy.orm.exc import NoResultFound

from miniworld.concurrency.ExceptionStopThread import ExceptionStopThread
from miniworld.errors import Unsupported
from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.network.connection import AbstractConnection
from miniworld.nodes.virtual.CentralNode import CentralNode
from miniworld.service.emulation import interface
from miniworld.service.persistence import nodes
from miniworld.service.persistence.nodes import NodePersistenceService
from miniworld.singletons import singletons
from miniworld.util import ConcurrencyUtil

__author__ = 'Nils Schmidt'

TIME_NODE_STATUS_REFRESH = 5


# TODO: RENAME TO NODES?
# TODO: REFACTOR!


class NodeStarter:
    """
    Starts the emulation nodes together with all its subcomponents.

    Attributes
    ----------
    node_ids : list<int>
        List of node IDs to start.
    nodes_running : list<Node>
    nodes : list<EmulationNode>
        List of started nodes.

    network_backend_name : str
    event_nodes_started : Event
    lock : Lock
    """

    def __init__(self, node_ids, network_backend_name):

        self._logger = singletons.logger_factory.get_logger(self)
        self.node_ids = node_ids
        self.nodes_running = []
        self.nodes = []

        self.network_backend_name = network_backend_name

        self.event_nodes_started = Event()

        self.lock = Lock()

        self.thread_check_nodes_started = None

        self._node_persistence_service = nodes.NodePersistenceService()
        self._interface_service = interface.InterfaceService()

    #################################################
    # Thread methods
    #################################################

    def print_overall_node_status(self):
        """ Print the nodes not ready yet """

        while not self.event_nodes_started.is_set():
            nodes_not_ready = self.nodes_not_ready()
            if nodes_not_ready:
                self._logger.info("waiting for nodes: %s ...", ', '.join(map(str, nodes_not_ready)))
                self.event_nodes_started.wait(TIME_NODE_STATUS_REFRESH)
            else:
                break

    # TODO: #51: suppliy node - interface - mapping
    # TOO: #82: DOC
    def start_nodes(self,
                    # node options
                    path_qemu_base_image, stringio_post_boot_script, interfaces=None,
                    ):
        """
        Start the nodes (a)synchronously.

        Parameters
        ----------
        path_qemu_base_image: str
        stringio_post_boot_script: StringIO, not file!
            If `parallel` each thread gets a copy!
        interfaces: list<str>
            NOTE: Influences the order of the network devices in the virtual machine!
        network_backend

        Returns
        -------
        list<EmulationNode>, ManagementNode
        """

        if not self.node_ids:
            self._logger.info("there are no nodes to start!")
            return [], None

        self.assert_only_one_wifibridge_interface(interfaces)

        # keep track of started nodes and print the missing ones each time unit ...
        self.thread_check_nodes_started = ExceptionStopThread.run_fun_threaded_n_log_exception(
            target=self.print_overall_node_status, tkwargs=dict(name="Nodes Start Progress"))
        self.thread_check_nodes_started.daemon = True
        self.thread_check_nodes_started.start()

        # NOTE: use same for sequential and parallel execution!
        stringio_post_boot_script.seek(0)
        # deepcopy StringIO (fails for file!)
        # NOTE: copying the :py:class:`.NetworkBackend` did not work, therefore we create a new copy each time
        try:
            # prepare arguments
            # NOTE: the creation of the network backend may rise an exception, therefore its inside thy try statement!
            args = []

            for i in self.node_ids:
                args.append((i,
                             path_qemu_base_image,
                             deepcopy(stringio_post_boot_script)
                             )
                            )
                # init events for first display
                singletons.event_system.init_events_for_node(i)

            # wait until all nodes have been started

            with ConcurrencyUtil.node_start_parallel() as executor:
                for node in executor.map(self._start_node, args):
                    self.nodes.append(node)

            self._logger.info("all qemu instances started ...")

            # NOTE: create management switch after all nodes exist!
            # TODO: return management node and not None if scenario changed
            management_node = None
            if singletons.simulation_manager.scenario_changed:
                management_node = self.start_management_node()

            return self.nodes, management_node

        finally:
            # stop thread
            self.event_nodes_started.set()
            self.thread_check_nodes_started.join()

    @staticmethod
    def assert_only_one_wifibridge_interface(interfaces):
        if len(list(filter(lambda x: CentralNode.is_central_node_interface(x), interfaces))) > 1:
            raise Unsupported("Multiple '%s' are not supported at the moment!" % Interface.InterfaceType.hub)

    # TODO: #82: DOC, maybe singleton ref?
    def start_management_node(self):
        """
        Start the management switch and connect all other nodes to it.
        Also store a reference in the :py:class:`.NetworkManager`.

        Returns
        -------
        ManagementNode
        """

        network_backend_bootstrapper = singletons.network_backend_bootstrapper
        if singletons.config.is_management_switch_enabled():
            # late import needed
            self._logger.info("creating management node/switch ...")
            if network_backend_bootstrapper.management_node_type is None:
                self._logger.info("Network Backend has no management node")
                return None

            # check if management node already exists
            try:
                return self._node_persistence_service.get(connection_type=AbstractConnection.ConnectionType.mgmt)._node
            except NoResultFound:
                node = Node(
                    interfaces=self._interface_service.factory([Interface.InterfaceType.management]),
                    type=AbstractConnection.ConnectionType.mgmt
                )

                # persist node
                self._node_persistence_service.add(node)

                management_node = network_backend_bootstrapper.management_node_type(node=node)
                management_node.start(switch=True, bridge_dev_name=singletons.config.get_bridge_tap_name())

                singletons.simulation_manager.nodes_id_mapping[node._id] = management_node

                for node in self.nodes:
                    management_node.connect_to_emu_node(singletons.network_backend, node)

                return management_node

    def _start_node(self, *args):
        """
        Start a node.

        Returns
        -------
        EmulationNode
        """
        args = args[0]
        node_id = args[0]  # type:int

        self._node_persistence_service = NodePersistenceService()

        add_node = True
        # if snapshot boot, do not add node again to db
        # node can not have changed since the scenario is still the same
        if not singletons.simulation_manager.scenario_changed:
            if self._node_persistence_service.exists(node_id):
                add_node = False

        if add_node:
            interfaces = deepcopy(singletons.scenario_config.get_interfaces(node_id=id))
            # automatically add a management interface if enabled in config
            if singletons.config.is_management_switch_enabled():
                interfaces.append(Interface.InterfaceType.management)

            assert isinstance(interfaces, list)
            interfaces = self._interface_service.factory(interfaces)
            node = Node(_id=node_id, interfaces=interfaces, type=AbstractConnection.ConnectionType.user)
            self._node_persistence_service.add(node)
        else:
            node = self._node_persistence_service.get(node_id=node_id)._node

        emulation_node = singletons.network_backend_bootstrapper.emulation_node_type(node)
        emulation_node.start(args[1], flo_post_boot_script=args[2])
        singletons.simulation_manager.nodes_id_mapping[node._id] = emulation_node

        with self.lock:
            # keep track of started nodes
            self.nodes_running.append(emulation_node)

        return emulation_node

    def nodes_not_ready(self):
        """
        Get all all nodes which have not started yet.
        Remembers the last started node id.

        Returns
        -------
        set<Node>
        """
        all_node_ids = set(self.node_ids)

        nodes_remaining = all_node_ids.difference(set(map(lambda node: node._node._id, self.nodes_running)))
        # all nodes started :)
        if not nodes_remaining:
            # remember last node id
            self.last_id = self.node_ids[-1]
            return set()

        return nodes_remaining
