import json
import logging
import random
import re

from StringIO import StringIO

from miniworld.Config import config
from miniworld.Scenario import scenario_config
from miniworld.errors import Base
from miniworld.repl.errors import REPLUnexpectedResult
from miniworld.util import PathUtil

__author__ = 'Nils Schmidt'

from miniworld.log import get_node_logger, get_file_handler

from miniworld.script.TemplateEngine import *
from miniworld.repl.REPLable import REPLable

class QemuMonitorSnapshotLoadError(Base):
    pass

class QemuMonitorRepl(REPLable):
    '''

    Qemu Monitor connection.

    Examples
    --------
    1. nils@ubuntu:~$ nc 127.0.0.1 1234
    ...QEMU 2.5.0 monitor - type 'help' for more information
    (qemu) savevm foo
    savevm foo
    (qemu)

    2.
    (qemu) info snapshots
    info snapshots
    ID        TAG                 VM SIZE                DATE       VM CLOCK
    1         foo                    152M 2016-10-19 16:47:23   00:00:20.694
    (qemu)

    Attributes
    ----------

    qemu : Qemu
        The associated Node.
    nlog
        Extra node logger.
    id : int
    '''

    def __init__(self, qemu):


        self.qemu = qemu

        # create extra node logger
        self.id = self.qemu.id
        self.nlog = get_node_logger(self.id)

        ################################
        # REPLable
        ################################

        REPLable.__init__(self)

        # unix domain socket paths
        self.path_uds_socket = self.get_qemu_sock_path(self.id)

    ###############################################
    ### Monitor Commands
    ###############################################

    def make_snapshot(self, name=None):
        if name is None:
            name = self.qemu.get_snapshot_id()
        self.run_commands_eager_check_ret_val(StringIO("savevm %s" % name))

    def loadvm(self, name):
        '''
        Load a snapshot.

        Parameters
        ----------
        name : str

        Raises
        ------
        QemuMonitorSnapshotLoadError
        '''
        try:
            if name is None:
                name = self.qemu.get_snapshot_id()
            self.run_commands_eager_check_ret_val(StringIO("loadvm %s" % name))
        except REPLUnexpectedResult as e:
            raise QemuMonitorSnapshotLoadError("Could not load '%s'" % name, caused_by=e)

    ###############################################
    ### REPLable
    ###############################################

    @staticmethod
    def get_qemu_sock_path(node_id):
        return PathUtil.get_temp_file_path("qemu_monitor_%s.sock" % node_id)

    def run_commands_eager_check_ret_val(self, flo, *args, **kwargs):
        def _return_value_checker(cmd, res):

            # TODO: this is only working for snapshot loading, is there a more generic approach?
            # QMP does not have to seem the needed features right now :/
            if re.search("Device '.*' does not have the requested snapshot '.*'", res):
                raise ValueError("Error!. Command: '%s', result:\n%s" % (cmd, res))

        return self.run_commands_eager(flo,
                                       *args,
                                       return_value_checker=_return_value_checker,
                                       **kwargs
                                       )

    def run_commands(self, flo, *args, **kwargs):
        '''
        Returns
        -------
        dict
        '''
        kwargs["timeout"] = config.get_repl_timeout()

        name = self.get_verbose_logger_path()

        kwargs.update({
            'brief_logger': self.nlog,
            'verbose_logger': self.verbose_logger,
            'shell_prompt' : '\\(qemu\\)',
            'enter_shell_send_newline' : False
        })
        res = REPLable.run_commands(self, flo, *args, **kwargs)
        # keep generator
        return res

#    def run_commands_eager(self, *args, **kwargs):
#        return [json.loads(sub_res) for sub_res in REPLable.run_commands_eager(self, *args, **kwargs)]

    def render_script_from_flo(self, flo):
        # overwrite default behaviour
        return flo.read()