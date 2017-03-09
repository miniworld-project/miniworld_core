import socket
import sys
from StringIO import StringIO
from itertools import repeat
from multiprocessing.pool import ThreadPool

from miniworld.Scenario import scenario_config
from miniworld.log import log
from miniworld.model.emulation.nodes.EmulationNode import EmulationNode
from miniworld.model.network.backends import NetworkBackends
from miniworld.model.network.interface import Interfaces

__author__ = 'Nils Schmidt'

# repl commands
REPL_CMD_EXIT = "myexit"
REPL_CMD_HELP = 'myhelp'
REPL_CMD_MODE = 'mymode'

# repl modes
REPL_MODE_QEMU = "qemu"
REPL_MODE_VDE = "vde"
REPL_MODE_WIREFILTER = "wirefilter"
REPL_MODES = REPL_MODE_QEMU, REPL_MODE_VDE, REPL_MODE_WIREFILTER

class REPL:
    '''
    Models a read-eval-print-loop for all given qemu nodes.

    A command can be executed on all qemu nodes either concurrently or sequentially.

    Attributes
    ----------
    nodes : list<Node>
        Nodes streamlined by the REPL.
    active_qemu_uds_sockets : list<socket>
        Active unix domain sockets connected to a qemu instance.
    async: bool, optional (default is False)
        Run commands concurrently
    mode : string, see `REPL_MODE_*` constants
        The active REPL mode.
    '''

    def __init__(self, number_of_nodes, async = False):
        '''
        Parameters
        ----------
        number_of_nodes: int
        async: bool, optional (default is False)
            Run commands concurrently
        '''
        # TODO: refactor to list<REPLable> ?


        # NOTE: give each node an own copy of the NetworkBackend and an own copy of the interfaces
        self.nodes = [EmulationNode(i,
                                    NetworkBackends.get_current_network_backend_bootstrapper().network_backend_type(NetworkBackends.get_current_network_backend_bootstrapper()),
                                    interfaces = Interfaces.Interfaces.factory_from_interface_names(scenario_config.get_interfaces())) for i in range(1, number_of_nodes + 1)]
        self.async = async
        self.active_qemu_uds_sockets = []
        self.mode = None

    def start(self):
        '''
        Start the read-eval-print-loop.
        CTRL-D and CTLR-C are forwarded to the qemu instances.
        '''

        log.info("starting interactive shell, streamlines commands to all qemu instances!")
        log.info("be sure to disconnect every instance connected to a qemu socket, otherwise this operations blocks!")
        log.info("Help: %s", self.fmt_help())
        log.info("enter '%s' to exit'", REPL_CMD_EXIT)

        # TODO: use lib for interactive shell stuff ?
        while 1:
            try:
                prompt = "$ "
                if self.mode:
                    prompt = '%s %s' % (self.mode, prompt)

                cmd = raw_input(prompt)
                uq_cmd = cmd.lower().strip()

                # always let print help and exit
                if uq_cmd == REPL_CMD_HELP:
                    print self.fmt_help()
                    continue
                elif uq_cmd == REPL_CMD_EXIT:
                    log.info("user quit session")
                    sys.exit(0)

                # mode chosen ?
                if uq_cmd.startswith(REPL_CMD_MODE):
                    # get value after "mode"
                    mode = filter(None, uq_cmd.split(REPL_CMD_MODE))[0].lower().strip()
                    if mode in REPL_MODES:
                        self.mode = mode
                        print "mode => %s" % mode
                    else:
                        print "Unknown mode '%s'" % mode
                else:
                    if self.mode is None:
                        print "Choose a mode first!"
                        continue
                    # may be empty or enter
                    elif cmd:
                        self._run_command_threaded(cmd)
                        log.info("executing '%s'", cmd)

            # CTRL-D
            except EOFError as e:
                log.info("sending CTRL-D (EOT) ...")
                self._run_command_interrupt('\x1a')
                log.info("sending CTRL-D (EOT) [done]")
            # CTLR-C
            except KeyboardInterrupt as e:
                log.info("sending CTRL-C instances ...")
                self._run_command_interrupt('\x03')
                log.info("sending CTRL-C instances [done]")

    def run_command(self, args):
        '''
        Runs the command on uds sockets.
        Before running the instance via a unix domain socket,
        the corresponding socket object is returned via a generator.

        This enabled, the latter closing of the socket, so that blocking commands can be interrupted.

        Parameters
        ----------
        cmd : str
        '''
        node, cmd = args

        # get unix domain socket before executing the commands
        # TODO: support all modes
        if self.mode == REPL_MODE_QEMU:
            uds_socket_gen = node.virtualization_layer.run_commands_get_socket(
                StringIO(cmd),
                interactive_result_stdout_writing = not self.async,
                logger = node.virtualization_layer.nlog
            )
        elif self.mode == REPL_MODE_VDE:
            uds_socket_gen = node.vde_switch.run_commands_get_socket(
                StringIO(cmd),
                interactive_result_stdout_writing = not self.async,
                logger = node.vde_switch.nlog
            )

        elif self.mode == REPL_MODE_WIREFILTER:
            # TODO:
            print "N/A"

        for uds_socket in uds_socket_gen:
            if isinstance(uds_socket, socket.socket):
                # store unix domain socket
                self.active_qemu_uds_sockets.append(uds_socket)
            else:
                # finished executing commands via uds socket...
                # clean up
                try:
                    self.active_qemu_uds_sockets.remove(uds_socket)
                except:
                    pass

    def _run_command_threaded(self, cmd):
        '''
        Runs the command `cmd` threaded. If `self.async` execute all concurrently, otherwise use a single thread.
        The single thread is needed so that the repl is not blocking.

        Parameter
        ---------
        cmd : str
            The command to execute in the qemu instance
        '''
        # one thread per node for async, else 1
        pool =  ThreadPool(processes = len(self.nodes) if self.async else 1)
        pool.map_async(self.run_command, zip(self.nodes, repeat(cmd)))

    def _run_command_interrupt(self, cmd):
        '''
        Simulate an interrupt. Close the active unix domain socket connections, so that `cmd` can be executed.
        Usefor for sending CTRL-D or CTRL-C to the qemu intances.
        '''
        to_remove = []

        # remember sockets
        for uds_sock in self.active_qemu_uds_sockets:
            to_remove.append(uds_sock)

        # after removing a socket, the uds socket provided by qemu does not block any more (allows one simultaneous connection)
        # therefore a waiting thread might be connecting, adding a new uds socket to `active_qemu_uds_sockets`
        # therefore we remember the active sockets one stop before
        for uds_sock in self.active_qemu_uds_sockets:
            try:
                # close connection immediately
                uds_sock.shutdown(socket.SHUT_RDWR)
                uds_sock.close()
                to_remove.append(uds_sock)

            except socket.error as e:
                log.exception(e)

        # remove all closed sockets
        for uds_sock in to_remove:
            try:
                self.active_qemu_uds_sockets.remove(uds_sock)
            except:
                pass

        # finally run command
        self._run_command_threaded(cmd)

    def fmt_help(self):
        '''
        Fmt a help string.
        '''
        return """Commands:
        %s        Print this help.
        %s <mode> Switch to a different mode, where mode in (%s).
        %s        Leave the REPL.
        """ % (REPL_CMD_HELP,
               REPL_CMD_MODE, ', '.join(REPL_MODES),
               REPL_CMD_EXIT)