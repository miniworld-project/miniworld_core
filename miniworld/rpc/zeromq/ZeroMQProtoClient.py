#!/usr/bin/env python3
import argparse
import json
import random
import sys
from pprint import pformat

import netifaces
import zmq

import miniworld
from miniworld.Config import config
from miniworld.Scenario import scenario_config
from miniworld.log import log
from miniworld.management import ServerScore
from miniworld.model.collections import DistanceMatrix
from miniworld.model.singletons.Resetable import Resetable
from miniworld.model.singletons.Singletons import singletons
from miniworld.rpc import Protocol
from miniworld.rpc.zeromq import States


def factory():
    '''
    Use the config system to choose the zeromq client type.

    Returns
    -------
    type
    '''
    if config.is_protocol_zeromq_mode_mcast():
        log.info("distance matrix distribution via publish-subscribe pattern")
        return ZeroMQClientSub
    else:
        log.info("distance matrix distribution via request-reply pattern")
        return ZeroMQClientReq

class ZeroMQException(BaseException):
    pass

class ZeroMQClient:

    '''
    This is a client for the :py:class:`.ZeroMQService` which uses a request socket.
    The socket is intended for synchronous communication in a blocking request-reply pattern.

    The communication between the client and the server is implemented as a state machine.
    This means, there are different states. The client includes in every message it's state and also it's node id.
    See :py:mod:`.Protocol`.

    In the first step, the client connects to the server and requests the server id. All following requests contain the server id
     to identify the client.

    The exact steps are:
    1. request node id and receive the node id
    2. send tunnel IP address and receive the scenario config
    3. Start the nodes and sync with the server
    4. Get the distance matrix in a loop. Implementation depends on the subclass

    Protocol:
    state | node id | arg_1 | ... | arg_n

    See Also
    --------
    http://rfc.zeromq.org/spec:28/REQREP/

    Attributes
    ----------
    server_addr : str
        IP of the server.
    context : zmq.sugar.context.Context
    svc : zmq.sugar.socket.Socket
        Req socket.
    reset_socket : zmq.sugar.socket.Socket
        Sub Socket.
    server_id : int
        The id of this emulation server / zeromq client
    tunnel_ip : str
        IP address.

    serialize : see :py:meth:`Protocol.serialize`
    deserialize : :py:meth:`Protocol.deserialize`
    '''
    def __init__(self, server_addr):
        self.server_addr = server_addr
        self.context = zmq.Context()

        self.init_req_socket()

        self.reset_socket = self.context.socket(zmq.SUB)
        self.reset_socket.setsockopt(zmq.SUBSCRIBE, '')
        self.reset_socket.setsockopt(zmq.IDENTITY, bytes(random.randrange(1, sys.maxint)))
        addr = "tcp://{}:{}".format(self.server_addr, Protocol.PORT_PUB_RESET_SERVICE)
        self.reset_socket.connect(addr)
        log.info("connecting to: %s ...", addr)

        self.server_id = None

        self.serialize = singletons.protocol.serialize
        self.deserialize = singletons.protocol.deserialize

        self.tunnel_ip = None

    def init_req_socket(self):
        addr = 'tcp://{}:{}'.format(self.server_addr, Protocol.PORT_DEFAULT_SERVICE)
        log.info("connecting to: %s ...", addr)
        self.svc = self.context.socket(zmq.REQ)
        # self.svc.setsockopt(zmq.REQ_CORRELATE, 1)
        # self.svc.setsockopt(zmq.REQ_RELAXED, 1)
        self.svc.connect(addr)

    # def reset(self):
    #     #self.reset_socket.close()
    #     self.svc.close()
    #     self.init_req_socket()

    # TODO: create own logger!
    def myprint(self, str):
        '''
        Include the server id in log messages
        Parameters
        ----------
        str : str
        '''
        log.info('%s: %s', self.server_id, str)

    #####################################################################
    ### Sending and receiving
    #####################################################################

    def send_server_id(self, state, *args):
        '''
        Send a message including the server id.

        Parameters
        ----------
        state : str
        args : list<obj>

        '''
        # let server id be the first message part
        self.send_multi_part(state, self.server_id, *args)

    def send_multi_part(self, *args):
        self.svc.send_multipart(
            list(map(self.serialize, args))
        )

    def send_no_server_id(self, *args):
        '''
        Send a message exluding the server id

        Parameters
        ----------
        args
        '''
        self.send_multi_part(*args)

    def recv(self):
        '''
        Receive a message and deserialize it with the current protocol.

        Returns
        -------
        obj
        '''

        return self.deserialize(self.svc.recv())

    #####################################################################
    ### State handling
    #####################################################################

    def start(self, tunnel_ip):
        '''
        This method contains steps 1-3.

        Parameters
        ----------
        tunnel_ip : str

        Returns
        -------
        scenario_config : str
            The scenario config as json.
        '''

        self.tunnel_ip = tunnel_ip

        #########################################################
        ### State: Register
        #########################################################

        self.myprint("registering at server ...")

        self.send_no_server_id(States.STATE_REGISTER)
        if config.is_debug():
            self.myprint("registering at server [done]")
        server_id = self.recv()

        self.server_id = server_id

        self.myprint("server id is: %d" % int(server_id))

        # TODO: RENAME state!
        #########################################################
        ### State: Information exchange
        #########################################################

        server_score = ServerScore.factory()()

        self.send_server_id(States.STATE_EXCHANGE, tunnel_ip, server_score.get_score())

        scenario_config = json.dumps(self.recv())
        self.myprint("scenario config: %s" % pformat(scenario_config))

        #########################################################
        ### State: Start Nodes
        #########################################################

        self.myprint("starting nodes")
        self.start_nodes(scenario_config)

        self.send_server_id(States.STATE_START_NODES)
        self.myprint("syncing with other nodes ...")
        self.recv()
        self.myprint("synced with other nodes ...")

        return scenario_config

    #####################################################################
    ### Helpers
    #####################################################################

    def start_nodes(self, scenario_config_json):
        # NOTE: we need json here
        log.info("starting nodes ...")
        singletons.simulation_manager.start(scenario_config_json)

class ZeroMQClientReq(ZeroMQClient):

    '''
    This subclass implements step 4 by receiving the local distance matrix via the request socket.
    NOTE: the client does not see the whole distance matrix!
    '''
    def start(self, tunnel_ip):
        # do steps 1-3
        scenario_config = super(ZeroMQClientReq, self).start(tunnel_ip)

        #########################################################
        ### State: Distance Matrix
        #########################################################

        # wait for new distance matrices ...
        self.enter_run_loop()

    def enter_run_loop(self):
        while 1:
            self.send_server_id(States.STATE_DISTANCE_MATRIX)

            distance_matrix = self.recv_distance_matrix()

            # did not receive individual matrix
            if not config.is_publish_individual_distance_matrices():
                distance_matrix = singletons.simulation_manager.get_local_distance_matrix_to_servers(distance_matrix)

            if config.is_debug():
                self.myprint("distance matrix: %s" % distance_matrix)
            singletons.simulation_manager.step(1, distance_matrix=distance_matrix)

    def recv_distance_matrix(self):
        '''
        Receive the distance matrix and detransform it to its actual form.

        Returns
        -------
        DistanceMatrix
        '''

        return DistanceMatrix.factory()(DistanceMatrix.detransform_distance_matrix(self.recv()))

class ZeroMQClientSub(ZeroMQClient, Resetable):

    '''
    This client receives the whole distance matrix from a publish-subscribe socket.
    Therefore, the client is responsible for cutting out the necessary part of the distance matrix.

    To sync with the server, the request socket sends a request in the distance matrix state.
    Afterwards it receives the distance matrix via the publish-subscribe socket.
    Attributes
    ----------
    sub_socket : zmq.sugar.socket.Socket
    '''

    def __init__(self, *args, **kwargs):
        super(ZeroMQClientSub, self).__init__(*args, **kwargs)

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, '')

        addr = "tcp://{}:{}".format(self.server_addr, Protocol.PORT_PUB_SERVICE)
        self.sub_socket.connect(addr)
        log.info("connecting to: %s ...", addr)

    def start(self, tunnel_ip):
        scenario_config = super(ZeroMQClientSub, self).start(tunnel_ip)

        #########################################################
        ### State: Distance Matrix
        #########################################################

        self.enter_run_loop()

    def sync(self):
        '''
        Sync with the server. Stay in state distance matrix
        '''

        self.send_sync()
        self.recv_sync()

    def send_sync(self):
        log.info("syncing with server ...")
        self.send_server_id(States.STATE_DISTANCE_MATRIX)

    def recv_sync(self):
        if config.is_debug():
            log.debug("syncing with server [done]")
        self.recv()

    def recv_distance_matrix(self):
        '''
        Receive the whole distance matrix via the publish-subscribe socket and filter out the relevant part.

        Returns
        -------
        DistanceMatrix
        '''
        whole_distance_matrix = DistanceMatrix.detransform_distance_matrix(self.deserialize( self.sub_socket.recv() ))

        if config.is_debug():
            log.info("server id: %d", scenario_config.get_distributed_server_id())

        local_distance_matrix = singletons.simulation_manager.get_local_distance_matrix_to_servers(whole_distance_matrix)

        return DistanceMatrix.factory()(local_distance_matrix)

    # TODO: DOC
    def reset(self):
        log.info("got reset message ...")
        singletons.simulation_manager.abort()
        #super(ZeroMQClientSub, self).reset()
        self.start(self.tunnel_ip)

    # TODO: adjust doc for reset ...
    def enter_run_loop(self):
        '''
        Receive the updates of the distance matrix.

        Steps:
        1. Sync via the request socket with the server
        2. Receive from the publisher.

        Raises
        ------
        ZeroMQException
        '''
        log.info("entering run loop ...")

        # initial sync

        log.info("syncing with server initially ...")
        self.sync()

        # enable CTRL-C
        while 1:
            def step():

                #self.sync()
                rlist, _, xlist = zmq.select([self.reset_socket, self.sub_socket], [], [])

                def handle_select(rlist, xlist):

                    if xlist:
                        raise ZeroMQException("Unknown error occurred during a select() call")

                    if self.reset_socket in rlist:
                        self.reset_socket.recv()
                        self.reset()
                        return True

                    if self.sub_socket in rlist:
                        local_distance_matrix = self.recv_distance_matrix()
                        if config.is_debug():
                            log.info("received distance matrix: %s", local_distance_matrix)

                        log.info("step ...")

                        singletons.simulation_manager.step(1, distance_matrix=local_distance_matrix)

                        self.send_sync()
                        # wait for sync reply or error
                        rlist, _, xlist = zmq.select([self.reset_socket, self.svc], [], [])
                        #rlist, _, xlist = zmq.select([self.svc], [], [])

                        if handle_select(rlist, xlist):
                            return True

                        #self.sync()

                        if config.is_debug():
                            log.debug("stepped ...")

                    if self.svc in rlist:
                        self.recv_sync()
                        return True


                if handle_select(rlist, xlist):
                    return

            if step():
                return
            # exec_time = timeit(step, number=1)
            # log.info("took %0.2f seconds (sync + step)", exec_time)

if __name__ == '__main__':

    miniworld.init()

    parser = argparse.ArgumentParser(description='???')

    # at least one of the mutually exclusive arguments is required
    meg = parser.add_mutually_exclusive_group(required=True)
    meg.add_argument("-ta", "--tunnel-address", help="")
    meg.add_argument("-ti", "--tunnel-interface", help="")

    parser.add_argument("server_address", help="Address of the ZeroMQServer")

    args = parser.parse_args()
    if args.tunnel_address:
        tunnel_addr = args.tunnel_address
    else:
        # {2: [{'addr': '192.168.0.14',
        # 'broadcast': '192.168.0.255',
        # 'netmask': '255.255.255.0'}],
        # 18: [{'addr': 'a4:5e:60:ca:5c:0f'}]}
        tunnel_addr = netifaces.ifaddresses(args.tunnel_interface)[netifaces.AF_INET][0]['addr']

    server_addr = args.server_address
    log.info("server address: %s", server_addr)
    log.info("tunnel address: %s", tunnel_addr)

    zeromq_client = factory()(server_addr)
    zeromq_client.start(tunnel_addr)