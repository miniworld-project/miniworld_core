#!/usr/bin/env python3
import argparse
import random
import sys
import threading
import time
from pprint import pformat

import zmq

import miniworld
from miniworld import Scenario
from miniworld.Config import config
from miniworld.log import log
from miniworld.model.StartableObject import StartableObject
from miniworld.model.collections import DistanceMatrix
from miniworld.model.singletons.Singletons import singletons
from miniworld.rpc import Protocol
from miniworld.rpc.zeromq import States
from miniworld.rpc.zeromq.StateMachine import Expecter, ResponderArgument, ResponderServerID, ResponderPerServerID
from miniworld.util.CliUtil import scenario_config_parser, parse_scenario_config


def factory():
    if config.is_protocol_zeromq_mode_mcast():
        log.info("distance matrix distribution via publish-subscribe pattern")
        return ZeroMQCServerPubSub
    else:
        log.info("distance matrix distribution via request-reply pattern")
        return ZeroMQServerRouter

# TODO: use for experiments!
CNT_ZMQ_THREADS = 1


# TODO: if not all emulation servers are needed, these could be excluded from the current simulation, resulting in faster communication and less overhead
class ZeroMQServer(StartableObject):
    '''
    For an introduction to the zeromq services, see :py:class:`.ZeroMQClient`.

    '''
    def __init__(self):
        '''
        Parameters
        ----------
        context : zmq.sugar.context.Context
        router_socket : zmq.sugar.socket.Socket
            Router socket.
        reset_socket : zmq.sugar.socket.Socket
            Pub socket.
        protocol : Protocol
        cnt_peers : int
            The number of emulation servers to be expected.

        serialize : see :py:meth:`Protocol.serialize`
        deserialize : :py:meth:`Protocol.deserialize`

        wait_for_scenario_config : threading.Event
        wait_for_nodes_started : threading.Event

        last_step_time : int
        '''

        StartableObject.__init__(self)

        self.context = zmq.Context.instance(CNT_ZMQ_THREADS)

        # create the router socket
        self.router_socket = self.context.socket(zmq.ROUTER)
        addr = "tcp://*:{}".format(Protocol.PORT_DEFAULT_SERVICE)
        self.router_socket.bind(addr)
        # self.router_socket.setsockopt(zmq.REQ_CORRELATE, 1)
        # self.router_socket.setsockopt(zmq.REQ_RELAXED, 1)
        log.info("listening on '%s'", addr)


        # create the publish socket
        self.reset_socket = self.context.socket(zmq.PUB)
        self.reset_socket.setsockopt(zmq.IDENTITY, bytes(random.randrange(1, sys.maxint)))
        addr = "tcp://*:{}".format(Protocol.PORT_PUB_RESET_SERVICE)
        self.reset_socket.bind(addr)
        log.info("listening on '%s'", addr)

        self.protocol = Protocol.factory()()

        self.serialize = singletons.protocol.serialize
        self.deserialize = singletons.protocol.deserialize

        self.wait_for_scenario_config = threading.Event()
        self.wait_for_nodes_started = threading.Event()
        #self.reset_required = threading.Event()

        self.reset()

        log.info("node scheduler: '%s'", singletons.node_distribution_strategy.__class__.__name__)

    def reset(self):
        self.cnt_peers = None

        self.wait_for_nodes_started.clear()
        self.wait_for_scenario_config.clear()
        #self.reset_required.clear()

        self.last_step_time = None

    # TODO: DOC
    def send_reset(self):
        self.reset_socket.send(b'reset')
        # NOTE: we have to sync the subscribers to ensure they got the message
        #self.sync_subscribers()
        self.reset()

    def _start(self, cnt_peers):
        '''
        Start the server by expecting the clients to register in the first state.
        This method controls the whole communication expect the distribution of the distance matrix.

        Parameters
        ----------
        cnt_peers : int

        Returns
        -------

        '''
        log.info("waiting for %d servers ...", cnt_peers)
        self.cnt_peers = cnt_peers

        self.handle_state_register()

        # wait until the scenario config is set, because the tunnel addresses
        # (received in the next step) are written to it
        log.info("waiting until scenario config is set ...")
        self.wait_for_scenario_config.wait()
        self.handle_state_information_exchange()
        # TODO: let NetworkBackend inject communication steps for needed information
        self.handle_state_start_nodes()

    def _shutdown(self):
        log.info("sending reset to clients ...")
        self.send_reset()
        # NOTE: finally do the reset (as last command)
        self.reset()
        log.info("shutdown complete")

    def get_expecter_state(self, *args, **kwargs):
        return Expecter(self.router_socket, self.cnt_peers, self.protocol, *args, **kwargs)

    ####################################################################
    ### State handling
    ####################################################################

    def handle_state_register(self):
        '''
        Wait until all clients have been registered and sync them afterwards.
        '''

        # show registered clients ...
        def register_fun(expecter, idx, cnt):
            log.info("%d/%d clients registered", idx, cnt)

        # let clients register and sync them
        log.info("state: %s", States.STATE_REGISTER)
        expect_state = self.get_expecter_state(States.STATE_REGISTER, 0, after_response_fun=register_fun)
        ResponderServerID(self.router_socket, self.protocol, expect_state)()

    def handle_state_information_exchange(self):
        '''
        Let clients send their tunnel Ip addr and send each the scenario config.
        '''

        log.info("state: %s", States.STATE_EXCHANGE)

        expect_state = self.get_expecter_state(States.STATE_EXCHANGE, 3)
        expect_state.expect_for_all()

        tunnel_addresses_dict = expect_state.get_message_part_per_node_id(arg_nr=1)
        server_score_dict = expect_state.get_message_part_per_node_id(arg_nr=2)
        singletons.node_distribution_strategy.server_score = server_score_dict
        log.info("server scores: %s", pformat(server_score_dict))

        # set tunnel addresses in scenario config
        Scenario.scenario_config.set_network_backend_bridged_tunnel_endpoints(tunnel_addresses_dict)

        # create scenario configs
        node_ids = miniworld.Scenario.scenario_config.get_local_node_ids()

        # distribute nodes among emulation server
        server_node_mapping = singletons.node_distribution_strategy.distribute_emulation_nodes(node_ids, self.cnt_peers)
        log.info("nodes mapping: %s", pformat(server_node_mapping))
        log.info("nodes per server: %s", pformat({k:len(v) for k,v in server_node_mapping.items()}))

        # set server to node mapping before creating the scenario configs
        miniworld.Scenario.scenario_config.set_distributed_server_node_mapping(server_node_mapping)
        # create for each server a custom scenario config
        scenario_configs = singletons.simulation_manager.create_scenario_configs(server_node_mapping)
        responder = ResponderPerServerID(self.router_socket, self.protocol, expect_state, scenario_configs)
        responder.respond()

    def handle_state_start_nodes(self):
        '''
        Start the nodes and sync them afterwards. Finally notify that :py:meth:`.handle_state_distance_matrix` can continue.
        '''
        log.info("state: %s", States.STATE_START_NODES)
        expect_state = self.get_expecter_state(States.STATE_START_NODES, 1)
        ResponderArgument(self.router_socket, self.protocol, expect_state, b'')()
        self.wait_for_nodes_started.set()

    def sync_subscribers(self):
        '''
        Sync the subscribers and provide some debugging information about the sync progress (if debug mode)
        '''
        log.info("syncing subscribers ...")

        def fun(expecter, idx, cnt):
            log.debug("%d/%d clients synced ...", idx, cnt)

        # add some debug info
        after_response_fun = fun if config.is_debug() else lambda x,y,z : None

        expect_distance_matrix = self.get_expecter_state(States.STATE_DISTANCE_MATRIX, 1, after_response_fun)
        # sync clients and send each his distance matrix
        ResponderArgument(self.router_socket, self.protocol, expect_distance_matrix, b'')()
        log.info("syncing subscribers [done]")

    def handle_state_distance_matrix(self, distance_matrix):

        if self.last_step_time is not None:
            et = time.time() - self.last_step_time
            log.info("took %0.2f seconds (previous distribution + sync)", et)
        self.last_step_time = time.time()

        self.wait_for_nodes_started.wait()

        self._handle_state_distance_matrix(distance_matrix)

class ZeroMQServerRouter(ZeroMQServer):

    '''
    This class sends the distance matrix for each peer via the zeromq router socket.
    Each server gets only the local distance matrix which it needs.
    '''

    # # TODO: check for each server if the distance matrix has been changed?
    # def enter_run_loop(self, block=True):
    #     '''
    #     Send each server updates of the local distance matrix.
    #     '''
    #
    #     super(ZeroMQServerRouter, self).enter_run_loop()
    #
    #     def fun(distance_matrix_per_server):
    #         '''
    #
    #         Convert each distance matrix into a json encodable format and send it to the server directly.
    #
    #         Parameters
    #         ----------
    #         distance_matrix_per_server : dict<int, dict<(int, int), int>>
    #             For each server the distance matrix.
    #         '''
    #         # convert each distance matrix into a structure which is json encodable
    #         self.handle_state_distance_matrix(distance_matrix_per_server)
    #
    #     # get the distance matrix per server
    #     self.drun_loop = singletons.simulation_manager.start_distributed_runloop(fun, split_distance_matrix=True)
    #
    #     if block:
    #         # enable CTRL-C
    #         while 1:
    #             self.drun_loop.join(0.1)

    def _handle_state_distance_matrix(self, distance_matrix_per_server):
        '''
        Note: Called externally.

        Parameters
        ----------
        distance_matrix_per_server : dict<int, dict<(int, int), int>>
            For each server the distance matrix.
        '''

        log.info("syncing nodes ...")

        distance_matrix_per_server = dict(zip(distance_matrix_per_server.keys(),
                                              list(map(DistanceMatrix.transform_distance_matrix,
                                                  distance_matrix_per_server.values()))))

        expect_distance_matrix = self.get_expecter_state(States.STATE_DISTANCE_MATRIX, 1)
        # sync clients and send each his distance matrix
        ResponderPerServerID(self.router_socket, self.protocol, expect_distance_matrix, distance_matrix_per_server)()

        log.info("synced nodes and send distance matrix")

class ZeroMQCServerPubSub(ZeroMQServer):

    '''
    This class enables the distribution of the distance matrix via a publish-subscribe pattern.

    Changes in the distance matrix (depending on the config) are sent efficiently to all subscribers.
    Because the computation of the distance matrix shall take place live,
    we synchronize the subscribers after each step of the :py:class:`.SimulationManager`.

    See Also
    --------
    http://rfc.zeromq.org/spec:29/PUBSUB/

    Attributes
    ----------
    pub_socket : zmq.sugar.socket.Socket
    last_distance_matrix_hash : str
        The last hash of the distance matrix.
        Used to send only the distance matrix if it changed (configurable via the config system)
    '''

    last_distance_matrix_hash = ""

    def __init__(self, *args, **kwargs):
        super(ZeroMQCServerPubSub, self).__init__(*args, **kwargs)

        # create the publish socket
        self.pub_socket = self.context.socket(zmq.PUB)
        addr = "tcp://*:{}".format(Protocol.PORT_PUB_SERVICE)
        self.pub_socket.bind(addr)
        log.info("listening on '%s'", addr)

    def _shutdown(self):
        # finally call context.term()
        super(ZeroMQCServerPubSub, self)._shutdown()

    def send_distance_matrix(self, distance_matrix):
        '''
        Send the distance matrix via the publish socket.

        Parameters
        ----------
        distance_matrix : DistanceMatrix
        '''
        data = self.serialize(DistanceMatrix.transform_distance_matrix(distance_matrix))
        log.info("sending %f kbytes ...", len(data) / 1024.0)
        self.pub_socket.send( data )

    def _handle_state_distance_matrix(self, distance_matrix):
        # # sync initially
        if singletons.simulation_manager.current_step == 0:
            log.info("syncing clients initially ...")
            self.sync_subscribers()

        self.send_distance_matrix(distance_matrix)
        self.sync_subscribers()

    # def enter_run_loop(self, block=True):
    #     '''
    #     Notify subscribers about changes in the distance matrix.
    #     '''
    #
    #     super(ZeroMQCServerPubSub, self).enter_run_loop()
    #
    #     ZeroMQCServerPubSub.last_distance_matrix_hash = ""
    #
    #     def fun(whole_distance_matrix):
    #
    #         new_distance_matrix = True
    #         if config.is_publish_only_new_distance_matrices():
    #             new_distance_matrix_hash = hash(frozenset(whole_distance_matrix.items()))
    #
    #             if new_distance_matrix_hash != ZeroMQCServerPubSub.last_distance_matrix_hash:
    #                 new_distance_matrix = False
    #
    #         if new_distance_matrix:
    #             log.info("change in distance matrix ...")
    #
    #             self.handle_state_distance_matrix(whole_distance_matrix)
    #
    #             if config.is_publish_only_new_distance_matrices():
    #                 ZeroMQCServerPubSub.last_distance_matrix_hash = new_distance_matrix_hash
    #
    #             if config.is_debug():
    #                 log.debug("publishing distance matrix: %s", pformat(whole_distance_matrix))
    #         else:
    #             log.info("no change in distance matrix ... not publishing!")
    #
    #     self.drun_loop = singletons.simulation_manager.start_distributed_runloop(fun, split_distance_matrix=False)
    #     if block:
    #         # enable CTRL-C
    #         while 1:
    #             self.drun_loop.join(0.1)


def main(cnt_peers):
    zmq_server = factory()()
    zmq_server.start(cnt_peers)
    zmq_server.enter_run_loop()

if __name__ == '__main__':
    miniworld.init()
    # TODO: read and set scenario config through rpc system!
    parser = argparse.ArgumentParser(parents=[scenario_config_parser], conflict_handler='resolve',
                                     description='???')
    parser.add_argument("cnt", type=int, help="Use n containers for testing")

    # parse and set scenario config
    _, _, scenario_config = parse_scenario_config()

    args = parser.parse_args()

    main(args.cnt)