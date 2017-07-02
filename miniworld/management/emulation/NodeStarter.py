from copy import deepcopy
from threading import Lock, Event

from miniworld.Config import config
from miniworld.concurrency.ExceptionStopThread import ExceptionStopThread
from miniworld.errors import Unsupported
from miniworld.log import log
from miniworld.model.emulation.nodes.EmulationNode import EmulationNode
from miniworld.model.emulation.nodes.virtual.CentralNode import is_central_node_interface
from miniworld.model.emulation.nodes.virtual.ManagementNode import ManagementNode
from miniworld.model.network.backends import NetworkBackends
from miniworld.model.network.interface.Interface import HubWiFi
from miniworld.model.singletons.Singletons import singletons
from miniworld.util import ConcurrencyUtil

__author__ = 'Nils Schmidt'

TIME_NODE_STATUS_REFRESH = 5

# TODO: RENAME TO NODES?
# TODO: REFACTOR!
class NodeStarter:
    '''
    Starts the emulation nodes together with all its subcomponents: qemu, vde_switch

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
    '''
    def __init__(self, node_ids, network_backend_name):

        self.node_ids = node_ids
        self.nodes_running = []
        self.nodes = []

        self.network_backend_name = network_backend_name

        self.event_nodes_started = Event()

        self.lock = Lock()

        self.thread_check_nodes_started = None

    #################################################
    ### Thread methods
    #################################################

    def print_overall_node_status(self):
        ''' Print the nodes not ready yet '''

        while not self.event_nodes_started.is_set():
            nodes_not_ready = self.nodes_not_ready()
            if nodes_not_ready:
                log.info("waiting for nodes: %s ...", ', '.join(map(str, nodes_not_ready)))
                self.event_nodes_started.wait(TIME_NODE_STATUS_REFRESH)
            else:
                break

    #  TODO: #51: suppliy node - interface - mapping
    # TOO: #82: DOC
    def start_nodes(self,
                    network_backend,
                    # node options
                    path_qemu_base_image, stringio_post_boot_script, interfaces = None,
                    # start options
                    parallel = False,
                    ):
        '''
        Start the nodes (a)synchronously.

        Parameters
        ----------
        path_qemu_base_image: str
        stringio_post_boot_script: StringIO, not file!
            If `parallel` each thread gets a copy!
        parallel: bool, optional (default is False)
            Use threads to start the nodes concurrently.
        interfaces: list<str>
            NOTE: Influences the order of the network devices in the virtual machine!
        network_backend

        Returns
        -------
        list<EmulationNode>, ManagementNode
        '''

        if not self.node_ids:
            log.info("there are no nodes to start!")
            return [], None

        self.assert_only_one_wifibridge_interface(interfaces)

        # keep track of started nodes and print the missing ones each time unit ...
        self.thread_check_nodes_started = ExceptionStopThread.run_fun_threaded_n_log_exception(target = self.print_overall_node_status, tkwargs=dict(name="Nodes Start Progress"))
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

                # TODO:
                # for arg in args:
                #     future_list.append( executor.submit(self._start_node, arg) )
                #
                #     # do not block the main thread too long -> eanbles listening to ctrl-c
                #     while 1:
                #
                #         for f in future_list:
                #             if not f.done():
                #                 sleep(1)
                #                 break
                #             else:
                #                 # raises the threads exception
                #                 self.nodes.append(f.result())
                #         break

            log.info("all qemu instances started ...")

            # NOTE: create management switch after all nodes exist!
            management_node = self.start_management_node()

            return self.nodes, management_node

        finally:
            # stop thread
            self.event_nodes_started.set()
            self.thread_check_nodes_started.join()


    @staticmethod
    def assert_only_one_wifibridge_interface(interfaces):
        if len(list(filter(lambda x: is_central_node_interface(x), interfaces))) > 1:
            raise Unsupported("Multiple '%s' are not supported at the moment!" % HubWiFi)

    # TODO: #82: DOC, maybe singleton ref?
    def start_management_node(self):
        '''
        Start the management switch and connect all other nodes to it.
        Also store a reference in the :py:class:`.NetworkManager`.

        Returns
        -------
        ManagementNode
        '''

        network_backend_bootstrapper = NetworkBackends.get_current_network_backend_bootstrapper()
        if config.is_management_switch_enabled():
            # late import needed
            from miniworld.management.network.manager import NetworkManager
            log.info("creating management node/switch ...")
            if network_backend_bootstrapper.management_node_type is None:
                log.info("Network Backend has no management node")
                return None

            management_node = network_backend_bootstrapper.management_node_type(network_backend_bootstrapper)
            management_node.start(switch = True, bridge_dev_name=config.get_bridge_tap_name())
            for node in self.nodes:
                management_node.connect_to_emu_node(singletons.network_backend, node)
            NetworkManager.management_node = management_node

            return management_node

    def _start_node(self, *args):
        '''
        Start a node.

        Returns
        -------
        EmulationNode
        '''
        args = args[0]

        # TODO: #54,#55
        node = NetworkBackends.get_network_backend_bootstrapper_for_string(self.network_backend_name).emulation_node_type.factory(*args[:1])
        node.start(args[1], flo_post_boot_script=args[2])

        with self.lock:
            # keep track of started nodes
            self.nodes_running.append(node)

        return node

    def nodes_not_ready(self):
        '''
        Get all all nodes which have not started yet.
        Remembers the last started node id.

        Returns
        -------
        set<Node>
        '''
        all_node_ids = set(self.node_ids)

        nodes_remaining = all_node_ids.difference(set(map(lambda node: node.id, self.nodes_running)))
        # all nodes started :)
        if not nodes_remaining:
            # remember last node id
            self.last_id = self.node_ids[-1]
            return set()

        return nodes_remaining