#!/usr/bin/env python3

import argparse
import json
import sys
import xmlrpc.client

from miniworld import Constants, Config
from miniworld.Config import config
from miniworld.log import log
from miniworld.rpc import RPCUtil
from miniworld.util import CliUtil
from miniworld.util.CliUtil import rpc_parser


class Action():

    '''
    Models an action that is associated with a argparse parser.
    The class behaves like a function, but provides custom initialization.

    We use that to provide the rpc connection in any function and to check for errors in the simulation loop.

    Attributes
    ----------
    connection : xmlrpc.ServerProxy
    address : str
        The RPC connection address string.
    '''
    def __init__(self):
        self.connection = None

    @staticmethod
    def get_connection(addr):
        return xmlrpc.client.ServerProxy(addr, allow_none=True)

    def get_connection_server(self, node_id=None, server_id=None):

        if config.is_mode_distributed():

            # ask local rpc for ip of the server which holds the node

            if server_id is None and node_id is not None:
                server_id = self.connection.get_server_for_node(node_id)
            else:
                server_id = server_id

            print("using server: %s" % server_id, file=sys.stderr)
            addr = self.connection.get_distributed_address_mapping()[str(server_id)]
            addr = RPCUtil.addr_from_ip(addr, RPCUtil.PORT_CLIENT)
            log.info("switching to rpc server '%s'", addr)
            # drop local connection and use remote server
            connection = self.get_connection(addr)

            # check for errors first
            connection.simulation_encountered_exception()

            return connection

        # use local connection
        return self.connection

    def __call__(self, args, **kwargs):
        self.addr = RPCUtil.addr_from_ip(args.addr, RPCUtil.PORT_COORDINATOR)
        log.info("connecting to rpc server '%s'", self.addr)
        self.connection = self.get_connection(self.addr)
        if not args.no_check:
            # check for errors first
            self.connection.simulation_encountered_exception()

        # only switch to the rpc server which holds the node
        if hasattr(args, "node_id") and args.node_id is not None:
            self.connection = self.get_connection_server(node_id=args.node_id)

    def __new__(cls, *args, **kwargs):
        cls._instance = super(Action, cls).__new__(cls)
        return cls._instance(*args, **kwargs)

def new_action_decorator(fun):
    '''
    Models an Action class as method there the self paramter is supplied as first argument.

    Create
    Parameters
    ----------
    fun

    Returns
    -------
    ActionSubClass
    '''

    class ActionSubClass(Action):

        def __call__(self, *args, **kwargs):
            super(ActionSubClass, self).__call__(*args, **kwargs)

            # supply ActionSubClass to the method
            return fun(self, *args, **kwargs)

    return ActionSubClass

#################################################
### info
#################################################

@new_action_decorator
def action_info_addr(self, args):
    res = self.connection.get_distributed_address_mapping()
    if args.node_id:
        res = json.loads(res)[args.node_id]

    print(res)

@new_action_decorator
def action_info_server(self, args):
    node_id = args.node_id
    if node_id:
        return self.connection.get_server_for_node(node_id)
    else:
        return self.connection.get_distributed_node_mapping()

@new_action_decorator
def action_info_connections(self, args):
    print(self.connection.get_connections())

@new_action_decorator
def action_info_links(self, args):
    print(self.connection.get_links(args.include_interfaces))

@new_action_decorator
def action_info_distances(self, args):
    print(self.connection.get_distance_matrix())

@new_action_decorator
def action_info_scenario(self, args):
    print(self.connection.get_scenario())

# @new_action_decorator
# def action_info_shell_vars(self, args):
#     print self.connection.get_shell_variables(args.node_id)

#################################################
### ping
#################################################

@new_action_decorator
def action_ping(self, args):
    print(self.connection.ping())


#################################################
### logs
#################################################

@new_action_decorator
def action_logs_boot(self, args):
    print(json.loads(self.connection.node_get_qemu_boot_log(args.node_id)))

@new_action_decorator
def action_start(self, args):
    scenario_config, _ , scenario_config_json = CliUtil.parse_scenario_config(args.scenario_config, args.custom_scenario)

    if args.progress:
        return CliUtil.start_scenario(scenario_config_json, args.auto_stepping, blocking=False)

    return self.connection.simulation_start(scenario_config_json, args.auto_stepping)

@new_action_decorator
def action_stop(self, args):
    self.connection.simulation_abort()

@new_action_decorator
def action_step(self, args):
    return self.connection.simulation_step(args.steps)

@new_action_decorator
def action_exec(self, args, single=False):
    # TODO: we need to print deserialized json here due to the rpc server hack
    if not hasattr(args, "node_id"):
        node_id = None
    else:
        node_id = args.node_id

    cmds = args.cmds
    if single:
        cmds = ' '.join(cmds)
    else:
        cmds = '\n'.join(cmds)

    if node_id:
        # TODO: use kwargs
        print(json.loads(self.connection.exec_node_cmd(cmds, node_id, args.validate, args.timeout)))
    else:
        # only switch to the rpc server which holds the node
        for server_id in self.connection.get_distributed_address_mapping():
            self.connection = self.get_connection_server(server_id=server_id)
            print("%s >>>" % server_id, file=sys.stderr)
            print(json.loads(self.connection.exec_node_cmd(cmds, node_id, args.validate)))


@new_action_decorator
def action_shell(self):
    # TODO: we need to print deserialized json here due to the rpc server hack
    if not hasattr(args, "node_id"):
        node_id = None
    else:
        node_id = args.node_id

    cmds = args.cmds
    if single:
        cmds = ' '.join(cmds)
    else:
        cmds = '\n'.join(cmds)

    if node_id:
        print(json.loads(self.connection.exec_node_cmd(cmds, node_id, args.validate)))
    else:
        # only switch to the rpc server which holds the node
        for server_id in self.connection.get_distributed_address_mapping():
            self.connection = self.get_connection_server(server_id=server_id)
            print("%s >>>" % server_id, file=sys.stderr)
            print(json.loads(self.connection.exec_node_cmd(cmds, node_id, args.validate)))

if __name__ == '__main__':
    ACTION_START = "start"
    ACTION_STOP = "stop"
    ACTION_STEP = "step"

    ACTION_LOGS = "logs"
    ACTION_LOGS_BOOT = "boot"

    ACTION_EXEC = "exec"
    ACTION_EXEC_SINGLE = "execs"

    ACTION_PING = "ping"

    ACTION_INFO = "info"
    # ACTION_INFO_SHELL_VARS = "shell_vars"
    ACTION_INFO_ADDR = "addr"
    ACTION_INFO_SERVER = "server"
    ACTION_INFO_CONNECTIONS = "connections"
    ACTION_INFO_DISTANCES = "distances"
    ACTION_INFO_LINKS = "links"
    ACTION_INFO_SCENARIO = "scenario"

    root_parser = argparse.ArgumentParser(description='%s CLI' % Constants.PROJECT_NAME, parents=[rpc_parser], conflict_handler='resolve')
    root_parser.add_argument("--no-check", "-nc", action="store_true", help="Do not check for exceptions in the RunLoop first")
    subparser = root_parser.add_subparsers(help='Subcommands')

    def add_node_id_arg_optional(parser):
        parser.add_argument("--node-id", "-ni", help="The node id")

    def add_node_id_arg_positional(parser):
        parser.add_argument("node_id", help="The node id")

    def add_include_interfaces_optional(parser):
        parser.add_argument("--include-interfaces", "-ii", action="store_true", help="Show between which interfaces the connections are")


    def create_subparsers(subparser):
        info_parser = subparser.add_parser(ACTION_INFO)
        logs_parser = subparser.add_parser(ACTION_LOGS)
        start_parser = subparser.add_parser(ACTION_START)
        stop_parser = subparser.add_parser(ACTION_STOP)
        step_parser = subparser.add_parser(ACTION_STEP)
        exec_parser = subparser.add_parser(ACTION_EXEC)
        execs_parser = subparser.add_parser(ACTION_EXEC_SINGLE)
        ping_parser = subparser.add_parser(ACTION_PING)

        def create_info_parsers():
            info_subparser = info_parser.add_subparsers(help='Info Subcommands')

            # addr parser
            info_addr_parser = info_subparser.add_parser(ACTION_INFO_ADDR)
            add_node_id_arg_optional(info_addr_parser)
            info_addr_parser.set_defaults(func=action_info_addr)

            # server parser
            info_server_parser = info_subparser.add_parser(ACTION_INFO_SERVER)
            add_node_id_arg_optional(info_server_parser)
            info_server_parser.set_defaults(func=action_info_server)

            # connections parser
            connections_parser = info_subparser.add_parser(ACTION_INFO_CONNECTIONS)
            add_include_interfaces_optional(connections_parser)
            connections_parser.set_defaults(func=action_info_connections)

            # links parser
            link_parser = info_subparser.add_parser(ACTION_INFO_LINKS)
            add_include_interfaces_optional(link_parser)
            link_parser.set_defaults(func=action_info_links)

            # distances parser
            distances_parser = info_subparser.add_parser(ACTION_INFO_DISTANCES)
            distances_parser.set_defaults(func=action_info_distances)

            # shell variables
            # shell_vars_parser = info_subparser.add_parser(ACTION_INFO_SHELL_VARS)
            # add_node_id_arg_optional(shell_vars_parser)
            # shell_vars_parser.set_defaults(func=action_info_shell_vars)

            # scenario parser
            scenario_parser = info_subparser.add_parser(ACTION_INFO_SCENARIO)
            scenario_parser.set_defaults(func=action_info_scenario)

        def create_log_parsers():
            log_subparser = logs_parser.add_subparsers(help='Info Subcommands')
            boot_parser = log_subparser.add_parser(ACTION_LOGS_BOOT)
            add_node_id_arg_positional(boot_parser)
            boot_parser.set_defaults(func=action_logs_boot)


        def create_start_parsers():
            #start_subparser = logs_parser.add_subparsers(help='Info Subcommands')
            start_parser.add_argument("-cs", "--custom-scenario", help="Overrite settings in the senario file")
            start_parser.add_argument("-cc", "--custom-config", help="Overrite settings in the config file")
            start_parser.add_argument("-as", "--auto-stepping", action="store_true", default=False, help="If auto stepping is enabled, each concrete time interval a step is triggered. The default value is: %(default)s. If explicitly disabled, you have step manually.")
            start_parser.add_argument("-p", "--progress", action="store_true", default=False,
                                      help="Show the progress via the CLI.")
            start_parser.add_argument("scenario_config", help="The scenario config (.json) that describes the scenario you want to start.")
            start_parser.set_defaults(func=action_start)

        def create_stop_parsers():
            stop_parser.set_defaults(func=action_stop)

        def create_step_parsers():
            step_parser.add_argument("steps", nargs='?', default=1, help="The amount of steps you want to do. Default is: %(default)s")
            step_parser.set_defaults(func=action_step)

        def create_exec_parsers():
            add_node_id_arg_optional(exec_parser)
            exec_parser.add_argument("cmds", nargs="+", help="The commands to be executed on the node")
            exec_parser.add_argument("-v", "--validate", action="store_true", default=False, help="Validate the return code of the command. Default is: %(default)s")
            exec_parser.add_argument("-t", "--timeout", default=5,
                                     help="Time to wait for the command to complete. Default is: %(default)s")
            exec_parser.set_defaults(func=action_exec)

        def create_execs_parsers():
            add_node_id_arg_optional(execs_parser)
            execs_parser.add_argument("cmds", nargs="+", help="The command to be executed on the node")
            execs_parser.add_argument("-v", "--validate", action="store_true", default=False, help="Validate the return code of the command. Default is: %(default)s")
            execs_parser.set_defaults(func=lambda *args : action_exec(*args, single=True))

        def create_ping_parsers():
            # ping parser
            ping_parser.set_defaults(func=action_ping)

        create_start_parsers()
        create_stop_parsers()
        create_exec_parsers()
        create_execs_parsers()
        create_step_parsers()
        create_info_parsers()
        create_log_parsers()
        create_ping_parsers()

        return [info_parser, logs_parser]

    Config.set_global_config(Config.PATH_GLOBAL_CONFIG)
    create_subparsers(subparser)

    args = root_parser.parse_args()
    print("parser args: %s" % args, file=sys.stderr)

    # give the actions the option to print themselves to stdout
    if hasattr(args, 'func'):
        res = args.func(args)
        # but if a value is returned, print it here
        if res:
            print(json.dumps(res, indent=4))
