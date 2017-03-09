import logging
import os
from StringIO import StringIO

import re

import subprocess32

from miniworld.log import get_logger, get_file_handler
from miniworld.management.ShellHelper import fmt_cmd_template
from miniworld.model.ShellCmdWrapper import ShellCmdWrapper
from miniworld.model.emulation.InterfaceDependentID import InterfaceDependentID
from miniworld.model.emulation.nodes.EmulationNode import EmulationNode
from miniworld.model.network.backends.AbstractConnection import AbstractConnection
from miniworld.model.network.backends.vde import VDESwitch
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import *
from miniworld.model.singletons.Singletons import singletons
from miniworld.repl.REPLable import REPLable
from miniworld.util import PathUtil

__author__ = 'Nils Schmidt'

# NOTE: yields errors on MAC OS, but needed to set the port number
CMD_TEMPLATE_WIREFILTER = """
dpipe
    vde_plug -p {port_num_a} {vde_switch_sock_path_a} =
     wirefilter  -M {wirefilter_uds_socket_path} {wirefilter_params} =
    vde_plug -p {port_num_b} {vde_switch_sock_path_b}
"""

WIREFILTER_PROMPT = "VDEwf$"

_logger = None

# TODO: LOGGERS FOR REPL
def logger():
    global _logger
    if _logger is None:
        _logger = get_logger("WireFilter", handlers = [])
        _logger.addHandler(logging.FileHandler(PathUtil.get_log_file_path("wirefilter.txt")))
    return _logger

def ensure_successful(fun, *args, **kwargs):
    kwargs['name'] = 'Wirefilter'
    kwargs['hiccup_funs'] = [lambda x : "1000 Success" in x]
    # we have only hiccup if the function returns False
    kwargs['negate'] = True
    return VDESwitch.fix_hiccup(fun, *args, **kwargs)


class Wirefilter(AbstractConnection, ShellCmdWrapper, REPLable):
    '''
    Handles the starting of a Wirefilter instance between two nodes.

    Attributes
    ----------
    id : str
    nlog
        Extra node logger.
    node_a : EmulationNode
    node_b: EmulationNode
    interface_a : Interface
    interface_b : Interface
    '''

    def __init__(self, emulation_node_x, emulation_node_y, interface_x, interface_y):
        AbstractConnection.__init__(self, emulation_node_x, emulation_node_y, interface_x, interface_y)

        ################################
        # REPLable
        ################################

        REPLable.__init__(self)

        # unix domain socket paths
        self.path_uds_socket = self.get_wirefilter_uds_socket_path(self.emulation_node_x.id, self.emulation_node_y.id, self.interface_x, self.interface_y)
        # log file for qemu shell commands
        self.log_path_commands = PathUtil.get_log_file_path("wirefilter_commands_%s.txt" % self.id)

    ###############################################
    ### Subclassed methods
    ###############################################

    # TODO: #54,#55, adjust doc
    def start(self, start_activated = False):
        '''
        Start the wirefilter and put the plug on `port_a` on the first node,
         on `port_b` on the second.

        Parameters
        ----------
        start_activated  : bool, optional (default is False)
            Start the wirefilter active mode, letting all packets pass through.
        '''
        # TODO: #54,#55
        vde_switch_x = self.emulation_node_x.network_mixin.switches[self.interface_x]
        vde_switch_y = self.emulation_node_y.network_mixin.switches[self.interface_y]
        port_a = vde_switch_x.get_free_port()
        port_b = vde_switch_y.get_free_port()

        node_a_id = self.emulation_node_x.id
        node_b_id = self.emulation_node_y.id

        wirefilter_params = "-l 100" if not start_activated else ""

        # TODO: parse network->wirefilter attributes such as 802.11 standards
        # but not for management node!
        # TODO: fill in
        # wifi_standard_802_11_wirefilter_params = {
        #     "a" : "",
        #     "b" : "",
        #     "g" : "-b 54000",
        #     "n" : "",
        #     "ac" : "-b 300000"
        # }
        #
        # wifi_standard_802_11 = scenario_config.get_wirefilter_802_11()
        # wifi_standard_802_11 = wifi_standard_802_11.lower()
        # if wifi_standard_802_11 in wifi_standard_802_11_wirefilter_params:
        #     wirefilter_params += " %s" % wifi_standard_802_11_wirefilter_params[wifi_standard_802_11]

        wirefilter_command = CMD_TEMPLATE_WIREFILTER.format(
            # connect on last port so we know the port number (necessary to move to a specific VLAN)
            port_num_a = port_a,
            port_num_b = port_b,
            vde_switch_sock_path_a = VDESwitch.VDESwitch.get_vde_switch_sock_path(self.emulation_node_x_idid),
            vde_switch_sock_path_b = VDESwitch.VDESwitch.get_vde_switch_sock_path(self.emulation_node_y_idid),
            wirefilter_uds_socket_path = self.get_wirefilter_uds_socket_path(self.emulation_node_x.id, self.emulation_node_y.id, self.interface_x, self.interface_y),
            wirefilter_params = wirefilter_params
            )

        self.process = singletons.shell_helper.run_shell_async(
            str((node_a_id, node_b_id)),
            wirefilter_command,
            prefixes = [self.shell_prefix],
            # TODO: DOC
            supervise_process=False
        )

        # wait until uds reachable -> cables connected
        self.wait_until_uds_reachable()
        # TODO: #54,#55
        # move port to specific VLAN on both sides of the switch
        vde_switch_x.move_interface_to_vlan(port = port_a, interface = self.interface_x)
        vde_switch_y.move_interface_to_vlan(port = port_b, interface = self.interface_y)

        return True

    def adjust_link_quality(self, link_quality_dict):
        '''

        Parameters
        ----------
        link_quality_dict

        Returns
        -------
        '''
        # assumes only equal interfaces can be connected to each other
        bandwidth = link_quality_dict.get(LINK_QUALITY_KEY_BANDWIDTH)
        loss = link_quality_dict.get(LINK_QUALITY_KEY_LOSS)

        commands = []
        if bandwidth is not None:
            commands.append( self.fmt_cmd_bandwidth(bandwidth) )
            singletons.network_manager.set_bandwidth(self.emulation_node_x, self.emulation_node_y, bandwidth)
        if loss is not None:
            commands.append( self.fmt_cmd_loss(loss) )

        # TODO: # 15: REMOVE CONNECTIONS OR JUST SET INFINITE LOSS?
        # TODO:
        if loss == LINK_QUALITY_VAL_LOSS_ALL:
            # TODO: REMOVE CONNECTIONS ...
            pass
        # TODO: CHECK FOR SUCCESS
        commands = '\n'.join(commands)
        # TODO: OWN LOGGER?
        self.nlog.info("adjusting link quality: %s", commands)
        ensure_successful(self.run_commands_eager, StringIO(commands))


    ###############################################
    ### REPLable
    ###############################################

    def run_commands(self, *args, **kwargs):
        name = "%s_%s" % (self.id, self.__class__.__name__)

        kwargs.update({
            'brief_logger': self.nlog,
            'verbose_logger': self.verbose_logger,

            'shell_prompt' : re.escape(WIREFILTER_PROMPT)
        })
        return REPLable.run_commands(self, *args, **kwargs)

    ###############################################
    ### Link Quality Adjustment
    ###############################################

    def fmt_cmd_bandwidth(self, bandwidth):
        return "bandwidth %s" % bandwidth

    def fmt_cmd_loss(self, loss):
        return "loss %s" % loss

    ###############################################
    ### Other
    ###############################################

    # TODO: occ
    @staticmethod
    def get_wirefilter_uds_socket_path(node_a_id, node_b_id, interface_a, interface_b):
        return PathUtil.get_temp_file_path(
            "wirefilter_%s_%s.sock" % (InterfaceDependentID.get_interface_class_dependent_id(node_a_id, interface_a.node_class, interface_a.nr_host_interface),
                                       InterfaceDependentID.get_interface_class_dependent_id(node_b_id, interface_b.node_class, interface_b.nr_host_interface))
        )
