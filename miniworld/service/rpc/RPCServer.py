#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import logging
import netifaces
import os
import pprint
import sys
import threading
from collections import OrderedDict
from functools import wraps
from threading import Lock
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# set PYTHONPATH
sys.path.insert(0, os.getcwd())  # noqa
from miniworld.model.connections.JSONEncoder import ConnectionEncoder

from miniworld.mobility import MovementDirectorFactory
from miniworld.nodes.qemu.Qemu import Qemu
from miniworld.service.rpc import RPCUtil
from miniworld.service.zeromq import ZeroMQProtoClient, ZeroMQProtoServer

import miniworld
from miniworld.singletons import singletons
from miniworld.util import PathUtil, JSONConfig

__author__ = 'Nils Schmidt', 'Patrick Lampe'

RPC_LOG_FILE_PATH = "rpc_server"

# TODO: REMOVE
_logger = None


def to_json(fun):
    def wrap(*args, **kwargs):
        return json.dumps(fun(*args, **kwargs), indent=4)

    return wrap


# TODO: DOC
def escape_decorator(fun):
    def wrapper(*args, **kwargs):
        res = fun(*args, **kwargs)
        return ''.join(map(escape, res))

    return wrapper


def dec_requires_simulation_running(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        if singletons.simulation_manager and singletons.simulation_manager.running:
            return fun(*args, **kwargs)
        raise ValueError("Simulation not running yet!")

    return wrap


def escape(c):
    # skipt 0 - 31 (https://docs.python.org/2/library/xmlrpclib.html)
    if ord(c) >= 32:  # and ord(c) <= ord('z'):
        return c
    else:
        return ''


# TODO: DOC


def assert_node_id_is_int(fun):
    """
    Raises
    ------
    ValueError
    """

    # TODO: use wraps in all decorators!
    # @wraps(fun)
    def wrap(*args, **kwargs):
        node_id = args[1]

        if not isinstance(node_id, int):
            raise ValueError("Node id has to be an integer!")

        return fun(*args, **kwargs)

    return wrap


def node_id_2_int(fun):
    """
    Raises
    ------
    ValueError
    """

    # TODO: use wraps in all decorators!
    # @wraps(fun)
    def wrap(*args, **kwargs):
        node_id = args[1]

        return fun(args[0], int(node_id), *args[2:], **kwargs)

    return wrap


# TODO: DOC
def assert_simulation_manager_started(fun):
    """
    Raises
    ------
    RuntimeError
    """

    def wrap(*args, **kwargs):
        _self = args[0]
        simulation_manager = singletons.simulation_manager

        with _self.lock:
            if not simulation_manager.running:
                raise RuntimeError("Simulation not started yet!")

        return fun(*args, **kwargs)


# TODO: set response type to json in all method responses!
# TODO: refactor!!
class MiniWorldRPC:
    """
    Attributes
    ----------
    zmq_server : ZeroMQServer, default is None
        Only set in the distributed mode.
    lock

    """

    def __init__(self):
        self.lock = Lock()
        self._logger = singletons.logger_factory.get_logger(self)

    #########################################
    # RPC Rewrite
    #########################################

    def ping(self):
        return "pong"

    def get_shell_variables(self):
        return pprint.pformat(Qemu.get_repl_variables_static(1))

    @to_json
    @node_id_2_int
    def get_server_for_node(self, node_id):
        return singletons.simulation_manager.get_server_for_node(node_id)

    # @dec_requires_simulation_running
    def get_connections(self):
        return json.dumps(
            OrderedDict(sorted(singletons.network_manager.connection_store.get_connections_per_node().items())),
            indent=4, cls=ConnectionEncoder)

    @dec_requires_simulation_running
    def get_links(self, include_interfaces, key=None):
        return singletons.network_manager.connection_store.get_link_quality_matrix(
            include_interfaces=include_interfaces, key=key).to_json()

    @to_json
    @dec_requires_simulation_running
    def get_distributed_address_mapping(self):
        res = singletons.scenario_config.get_network_backend_bridged_tunnel_endpoints()
        if not res:
            return {1: RPCUtil.LOCAL_IP_V4}
        return res

    def get_scenario(self):
        return json.dumps(singletons.scenario_config.data)

    @dec_requires_simulation_running
    def exec_node_cmd(self, cmd, node_id=None, validation=None, timeout=None):
        # NOTE: we cannot use @node_id_2_int here because node_id is optional
        if node_id is not None:
            node_id = int(node_id)

        return json.dumps(
            singletons.simulation_manager.exec_node_cmd(cmd, node_id=node_id, validation=validation, timeout=timeout))

    @dec_requires_simulation_running
    def get_distributed_node_mapping(self):
        return json.dumps(singletons.scenario_configget_distributed_server_node_mapping(), indent=4)

    # TODO: requires first step!
    @dec_requires_simulation_running
    def get_distance_matrix(self):
        return json.dumps(
            OrderedDict(sorted(singletons.simulation_manager.distance_matrix.items())),
            indent=4, cls=ConnectionEncoder
        )

    def simulation_run_loop_encountered_exception(self):
        try:
            singletons.simulation_manager.raise_run_loop_exception()
        except Exception:
            # SimulationManager already cleaned up stuff -> no need for cleanup here too ...
            raise

    # TODO: DOC, difference to simulation_run_loop_encountered_exception
    def simulation_encountered_exception(self):
        for exception_tuple in singletons.simulation_errors:
            raise exception_tuple
        singletons.simulation_manager.raise_run_loop_exception()

    #########################################
    # Logs
    #########################################

    @dec_requires_simulation_running
    @node_id_2_int
    def node_get_qemu_boot_log(self, node_id):
        path = singletons.simulation_manager.nodes_id_mapping[node_id].virtualization_layer.log_path_qemu_boot

        with open(path, "r") as f:
            return json.dumps(f.read())

    #########################################
    # Distance/Link Quality
    #########################################

    @dec_requires_simulation_running
    def node_get_complete_distance_matrix(self):
        singletons.simulation_manager.movement_director.get_distances_from_nodes()

    @dec_requires_simulation_running
    def node_get_distances(self, node_id):
        return OrderedDict((k, v) for k, v in self.node_get_complete_distance_matrix() if k[1] == node_id)

    @dec_requires_simulation_running
    def node_get_link_qualities(self, node_id):
        return OrderedDict((k, v) for k, v in self.node_get_complete_link_quality_matrix() if k[1] == node_id)

    #########################################
    # Coordinates
    #########################################
    @dec_requires_simulation_running
    def get_all_node_coordinates(self):
        return singletons.simulation_manager.movement_director.get_coordinates_for_nodes()

    @dec_requires_simulation_running
    def get_geo_json_roads(self):
        return singletons.simulation_manager.movement_director.get_geo_json_for_roads()

    @dec_requires_simulation_running
    def get_geo_json_nodes(self):
        return singletons.simulation_manager.movement_director.get_geo_json_for_nodes()

    #########################################
    # js stuff
    #########################################

    def get_is_arma(self):
        return singletons.scenario_config.get_walk_model_name() == MovementDirectorFactory.TOPOLOGY_MODE_ARMA

    def get_geo_json_connections(self):
        return singletons.simulation_manager.movement_director.get_geo_json_for_connections()

    def get_max_connected_distance(self):
        """ The maximum range in which nodes are still connected. """
        res = singletons.simulation_manager.link_quality_model.max_connected_distance
        if res is None:
            return 0
        return res

    #########################################
    # Progress Stats
    #########################################

    def get_progress(self, *args):
        res = singletons.event_system.get_progress(*args)
        return res

    def simulation_get_scenarios(self):
        return ["scenario1", "scenario2"]


yappi_started = False


def signal_profiling_handler(signum, *args, **kwargs):
    """
    Use SIGUSR2 to start profiling. Second signal dumps the stats to file.
    """
    import yappi
    global yappi_started
    logging.getLogger().debug("SIGUSR2 error handler ...")

    if not yappi_started:
        # start the profiler
        yappi.start()
        yappi_started = True
        logging.getLogger().debug("starting profiling with yappi ...")
    else:
        logging.getLogger().debug("stopping profiling with yappi and dump profile files ...")

        pstats_funs = yappi.convert2pstats(yappi.get_func_stats())

        def dump_stats(pstat, name):

            path_profile = PathUtil.get_temp_file_path("miniworld_%s.stats" % name)
            pstat.dump_stats(path_profile)
            logging.getLogger().debug("dumped profile data to file '%s'" % path_profile)

        dump_stats(pstats_funs, "pstats_funs")

        yappi_started = False


class MiniWorldRPCClient(MiniWorldRPC):
    """
    Attributes
    ----------
    zeromq_client : ZeroMQClient
    zeromq_thread : Thread
    """

    def __init__(self, server_addr, tunnel_addr):
        super(MiniWorldRPCClient, self).__init__()

        self.zeromq_client = ZeroMQProtoClient.factory()(server_addr)
        self._logger.info("running zeromq client in background thread ...")
        self.zeromq_thread = threading.Thread(target=self.zeromq_client.start, args=[tunnel_addr])
        self.zeromq_thread.daemon = True
        self.zeromq_thread.start()


class MiniWorldRPCServer(MiniWorldRPC):
    """
    Attributes
    ----------
    zeromq_thread : Thread
    zmq_server : ZeroMQServer
    """

    def __init__(self):
        super(MiniWorldRPCServer, self).__init__()

        self.zmq_server = None
        if singletons.config.is_mode_distributed():
            self._logger.info("starting in distributed mode ...")
            self.zmq_server = ZeroMQProtoServer.ZeroMQServer.factory()()
            singletons.zeromq_server = self.zmq_server

            self.start_zmq_thread()

    def start_zmq_thread(self):
        self.zeromq_thread = threading.Thread(target=self.__zeromq_server_start)
        self.zeromq_thread.daemon = True
        self.zeromq_thread.start()

    #########################################
    # ZeroMQ
    #########################################

    def __zeromq_server_start(self):
        self.zmq_server.start(singletons.config.get_mode_distributed_get_cnt_servers())

    #########################################
    # Simulation Control
    #########################################

    # TODO: reset if error occured during simulation start
    def simulation_start(self, scenario_config_content: str, auto_stepping, force_snapshot_boot=False):

        if singletons.config.is_mode_distributed():
            self._logger.info("starting in distributed mode ...")
        else:
            self._logger.info("starting in local mode ...")

        scenario_config: Dict = JSONConfig.read_json_config(scenario_config_content, raw=True)
        singletons.simulation_manager.start(scenario_config, auto_stepping=auto_stepping,
                                            force_snapshot_boot=force_snapshot_boot)

    def simulation_pause(self):
        singletons.simulation_manager.pause()

    def simulation_resume(self):
        pass

    def simulation_abort(self):
        singletons.simulation_manager.abort()

        if self.zmq_server:
            self._logger.debug("zmq shutdown ...")
            self.zmq_server.shutdown()
            self._logger.debug("zmq shutdown [done]")

        if self.zmq_server:
            self._logger.info("restarting zmq server ...")
            # self.__zeromq_server_start()
            self.start_zmq_thread()

    @dec_requires_simulation_running
    @node_id_2_int
    def simulation_step(self, steps):
        try:
            singletons.simulation_manager.step(steps)
        except Exception as e:
            self._logger.exception(e)
            raise


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


MODE_SERVER = "server"
MODE_CLIENT = "client"


def mode_server(args):
    singletons.config.set_is_coordinator(False)

    if args.tunnel_address:
        tunnel_addr = args.tunnel_address
    elif args.tunnel_interface:
        # {2: [{'addr': '192.168.0.14',
        # 'broadcast': '192.168.0.255',
        # 'netmask': '255.255.255.0'}],
        # 18: [{'addr': 'a4:5e:60:ca:5c:0f'}]}
        tunnel_addr = netifaces.ifaddresses(args.tunnel_interface)[netifaces.AF_INET][0]['addr']
    else:
        raise ValueError('Address required')

    coordinator_address = args.coordinator_address
    logging.getLogger().info("coordinator address: %s", coordinator_address)
    logging.getLogger().info("tunnel address: %s", tunnel_addr)
    return MiniWorldRPCClient, [coordinator_address, tunnel_addr], {}


def mode_coordinator(args):
    singletons.config.set_is_coordinator(True)

    return MiniWorldRPCServer, [], {}


def main():
    root_parser = argparse.ArgumentParser(description='MiniWorld network emulator')
    root_parser.add_argument('-c', '--config', default=os.environ.get('MW_CONFIG'), help="The config file")

    mode_group = root_parser.add_argument_group('mode')
    mode_group.add_argument('--distributed', action='store_true', help='Run in the distributed mode')
    mode_group.add_argument('--server', action='store_true',
                            help='Run as server. By default run as the coordinator in the distributed mode. Only works with --distributed')

    server_group = root_parser.add_argument_group('server')
    address_group = server_group.add_mutually_exclusive_group()
    # at least one of the mutually exclusive arguments is required
    address_group.add_argument("-ta", "--tunnel-address", help="")
    address_group.add_argument("-ti", "--tunnel-interface", help="")

    server_group.add_argument("--coordinator-address", "-ca", help="Address of the ZeroMQServer")

    args = root_parser.parse_args()

    # first create config since the mode_* functions need it
    config_path = os.path.abspath(args.config) if args.config is not None else None
    miniworld.init(config_path=config_path, do_init_singletons=True)

    # create the server or client rpc class, store in the global config if this is a coordinator or client
    if args.server:
        rpc_type, rpc_args, rpc_kwargs = mode_server(args)
    else:
        rpc_type, rpc_args, rpc_kwargs = mode_coordinator(args)

    # the singletons rely on the mode set in the argparser func
    miniworld.init_singletons()
    rpc_instance = rpc_type(*rpc_args, **rpc_kwargs)

    ip, port = "0.0.0.0", RPCUtil.get_rpc_port()
    logging.getLogger().info('running server at {}:{}'.format(ip, port))
    server = SimpleXMLRPCServer((ip, port),
                                requestHandler=RequestHandler,
                                logRequests=True,
                                allow_none=True)
    # addr=(socket.gethostbyname(socket.gethostname()), PORT))
    server.register_instance(rpc_instance)

    # TODO:
    if singletons.config.is_debug():
        logging.getLogger().debug("using yappi profiler ...")
        import signal

        # use signal handler to dump profiling results
        sig = signal.SIGUSR2
        signal.signal(sig, signal_profiling_handler)
        logging.getLogger().debug("installed signal handler for signal %s" % sig)

        # TODO: REMOVE
        # import rpdb2
        # rpdb2.start_embedded_debugger("asdf")

    logging.getLogger().info("rpc server running")
    logging.getLogger().debug("registered functions: %s", pprint.pformat(server.system_listMethods()))
    server.serve_forever()


if __name__ == '__main__':
    main()
