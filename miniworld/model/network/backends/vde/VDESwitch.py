import random
import re
from io import StringIO

from miniworld import log
from miniworld.errors import Base
from miniworld.log import get_logger, get_file_handler
from miniworld.model.ShellCmdWrapper import ShellCmdWrapper
from miniworld.model.network.backends.AbstractSwitch import AbstractSwitch
from miniworld.model.network.backends.vde.VDEConstants import PORT_QEMU
from miniworld.model.singletons.Singletons import singletons
from miniworld.repl.REPLable import REPLable
from miniworld.script.TemplateEngine import render_script_from_flo
from miniworld.util import PathUtil

__author__ = "Nils Schmidt"

CMD_TEMPLATE_VDE_SWITCH_NUM_PORTS = "port/setnumports {}"

# use hub for more realistic wifi and include the tap device
CMD_TEMPLATE_VDE_SWITCH = """
vde_switch
    -sock "{}"
    -M {}
    {switch_or_hub}
    {user_additions}
"""

CMD_TEMPLATE_VDE_VLAN = """
vlan/create {vlan}
port/setvlan {port} {vlan}
"""

# colors the port where the qemu instance is connected to the vde switch
# simulates hop to hop network (like mesh)
CMD_TEMPLATE_VDE_SWITCH_COLOR = """
port/setcolourful 1
port/setcolour {port} {color}
"""

# TODO: REMOVE


def get_num_tap_devices():
    ''' Get the number of tap devices associated with this switch '''
    return len(re.findall("-t", CMD_TEMPLATE_VDE_SWITCH))


class VDESWitchHiccup(Base):
    pass

# TODO: USE CONTEXTMANAGER? COULD BE MORE INTUITIVE!


def fix_vdeswitch_hiccup(fun, *args, **kwargs):
    kwargs['name'] = 'VDESwitch'
    return fix_hiccup(fun, *args, **kwargs)


def fix_hiccup(fun, *args, **kwargs):
    ''' Fix a bug of the VDESwitch where it responds with "Function not implemented"
    instead of the expected result.
    Trying it n times seems to be a workaround for now (Ticket #29)

    The method calls the function with its arguments.

    Parameters
    ----------
    kwargs['hiccup_funs'] : list<fun : str ->bool> , optional (default function checks for output 'Function not implemented')
        The hiccup check functions. If any matches we have a hiccup and repeat n times.
    kwargs['name'] : str
    kwargs['negate'] : bool, default is False
        Negate the result of the fun(...) call.

    Raises
    ------
    VDESWitchHiccup
    '''

    hiccup_funs = kwargs.get('hiccup_funs', [lambda output: "Function not implemented" in output])
    name = kwargs.get('name', "?")
    remove_kwargs = ['hiccup_funs', 'name', 'negate']
    negate = kwargs.get("negate", False)

    def negate_fun(x): return not x if negate else x

    for rm_kwarg in remove_kwargs:
        if rm_kwarg in kwargs:
            kwargs.pop(rm_kwarg)

    TRIES = 100
    i = 0
    while True:

        output = fun(*args, **kwargs)
        hiccup = False
        for hiccup_fun in hiccup_funs:
            if negate_fun(hiccup_fun(output)):
                hiccup = True
                log.warn("%s did not respond properly (hiccup:)", name)
                break

        if not hiccup:
            return output

        if i == TRIES:
            raise VDESWitchHiccup("%s responded with: '%s'! This is not the expected result (tried: %s times)!" % (name, output, i))
        i += 1


# TODO: #54,#55: REMOVE
class TapSwitch(AbstractSwitch):
    def __init__(self, id, interface):
        '''
        Parameters
        ----------
        id : int
        interface : Interface
        colorful : bool
            If the interface shall be colored on the switch.
        '''
        super(VDESwitch, self).__init__(id, interface)


class VDESwitch(AbstractSwitch, ShellCmdWrapper, REPLable):
    ''' Model around the `vde_switch` command.

     Attributes
     ----------
     id : str
     interface : Interface
     mgmt_dev_created : bool
     bridge_dev_name : bool
     '''

    def __init__(self, id, interface):
        '''
        Parameters
        ----------
        id : int
        interface : Interface
        colorful : bool
            If the interface shall be colored on the switch.
        '''
        super(VDESwitch, self).__init__(id, interface)

        # TODO: DOC
        # TODO: move to abstract class

        self.colorful = True

        # unix domain socket paths
        self.path_vde_switch_sock = self.get_vde_switch_sock_path(self.id)

        self.mgmt_dev_created = False
        self.bridge_dev_name = None

        ################################
        # REPLable
        ################################

        REPLable.__init__(self)

        # vde uds management socket
        self.path_uds_socket = self.get_vde_switch_mgmt_sock_path(self.id)

    def __str__(self):
        return '%s(%s, colorful=%s)' % (self.__class__.__name__, self.id, self.colorful)

    # TODO: move to abstract class
    def run_shell(self, cmd, *args, **kwargs):
        return singletons.shell_helper.run_shell(self.id, cmd, prefixes=[self.__class__.__name__])

    ###############################################
    # Subclass stuff
    ###############################################

    # TODO: #54,#55: check arguments. Should be wrong :/
    def _start(self, bridge_dev_name=None, switch=False):
        '''

        Parameters
        ----------
        bridge_dev_name : str, optional (default is None)
            The name of the device to bridge to.
            If None, don't bridge at all.
        switch : bool, optional (default is False)
            Start as switch. Otherwise as hub.

        Returns
        -------

        Raises
        ------
        NetworkBridgeNotExisting
        '''
        # TODO: do not allow command-line injection!
        # NOTE: create device before superclass checks for existence!
        self.bridge_dev_name = bridge_dev_name
        if self.bridge_dev_name:
            self.run_shell("ip tuntap add dev %s mode tap" % self.bridge_dev_name)
            self.mgmt_dev_created = True
        super(VDESwitch, self)._start(bridge_dev_name=self.bridge_dev_name, switch=switch)

        # bridge the vde switch to a specific device
        # TODO: Ticket #22 : Check if device is present on host
        user_additions = "-tap %s -m 666" % bridge_dev_name if bridge_dev_name is not None else ""
        # note: vde_switch has to be created before starting the qemu instance !
        vde_switch_command = CMD_TEMPLATE_VDE_SWITCH.format(self.path_vde_switch_sock, self.path_uds_socket,
                                                            switch_or_hub="" if switch else "-hub",
                                                            # TODO:
                                                            user_additions=user_additions)

        # start commands as subprocess
        # TODO: gitlab #2
        # TODO:
        self.process = singletons.shell_helper.run_shell_async(self.id, vde_switch_command, prefixes=[self.shell_prefix])

        # TODO:
        self.wait_until_uds_reachable()

    def reset(self):
        if self.mgmt_dev_created:
            self.run_shell("ip l del {}".format(self.bridge_dev_name))

    ###############################################
    # Custom Switch Stuff
    ###############################################

    # TODO: MOVE TO VDESWITCH
    def move_interface_to_vlan(self, interface, port=None):
        '''
        Move the port from the switch to a specific VLAN

        Parameters
        ----------
        port : int, optional (default is None)
        interface : Interface
        '''
        self.nlog.info("moving port %s to vlan %s", port, interface.node_class)
        fix_vdeswitch_hiccup(
            self.run_commands_eager,
            # node class interfaces are on the same VLAN
            StringIO(CMD_TEMPLATE_VDE_VLAN.format(port=port, vlan=interface.node_class))
        )

    def color_interface(self, port, color):
        '''
        Color the interface.
        '''

        if self.colorful:
            self.nlog.info("coloring qemu vde_switch port ...")
            # set color on first port on each switch (remember: one switch per interface)
            fix_vdeswitch_hiccup(
                self.run_commands_eager,
                StringIO(CMD_TEMPLATE_VDE_SWITCH_COLOR.format(port=port, color=color))
            )

    def get_used_ports(self):
        '''
        Get the used ports of the switch (there a cable is plugged into)

        Returns
        -------
        list<int>
        '''

        output = fix_vdeswitch_hiccup(self.run_commands_eager, StringIO("port/print"))
        return [int(port) for port in re.findall('Port\s+(\d+)', output)]

    def get_num_ports(self):
        ''' Get the number of ports the switch has '''

        output = fix_vdeswitch_hiccup(self.run_commands_eager, StringIO("port/showinfo"),
                                      hiccup_funs=[lambda output: "Function not implemented" in output,
                                                   lambda output: re.search("^\s+vde", output) is not None])

        return int(re.search("Numports=(\d+)", output).groups()[0])

    def get_free_port(self):
        ''' Get a free port '''
        possible_ports = set(range(PORT_QEMU, self.get_num_ports() + 1))
        used_ports = set(self.get_used_ports())
        # remove used ports
        possible_ports = list(possible_ports.difference(used_ports))

        # get port
        random_idx = random.randint(0, len(possible_ports) - 1)
        random_port = possible_ports[random_idx]
        return random_port

    def set_port_size(self, size):
        '''
        Set the number of ports for the switch.
        '''
        fix_vdeswitch_hiccup(self.run_commands_eager,
                             StringIO(CMD_TEMPLATE_VDE_SWITCH_NUM_PORTS.format(size)))

    @staticmethod
    def get_vde_switch_mgmt_sock_path(id):
        ''' Get the VDESwitch management unix domain socket path.

        Parameters
        ----------
        id : str
            Use :py:meth:`.get_vde_switch_id`
            to determine the vde switch id from the node id.

        Returns
        -------
        str
        '''
        return PathUtil.get_temp_file_path("vde_switch_mgmt_%s" % id)

    @staticmethod
    def get_vde_switch_sock_path(id):
        ''' Get the VDESwitch control unix domain socket path.

        Parameters
        ----------
        id : str
            Use :py:meth:`.get_vde_switch_id`
            to determine the vde switch id from the node id.

        Returns
        -------
        str
        '''
        return PathUtil.get_temp_file_path("vde_switch_%s" % id)

    ###############################################
    # REPLable
    ###############################################

    def run_commands(self, *args, **kwargs):
        name = "%s_%s" % (self.id, self.__class__.__name__)

        kwargs.update({
            'shell_prompt': re.escape("vde$"),
            # needed to see the executed commands in the log file
            'logger_echo_commands': True,
            'brief_logger': self.nlog,
            'verbose_logger': get_logger('verbose_%s' % name, handlers=[get_file_handler(name)]),
        })
        return REPLable.run_commands(self, *args, **kwargs)

    def render_script_from_flo(self, flo, **kwargs):
        '''
        Render the script from the file-like-object and inject some variables like ip addr and node id.

        Returns
        -------
        str
        '''

        return render_script_from_flo(flo,
                                      # TODO: fill dictionary for custom template (if needed at a later time
                                      **{
                                      }
                                      )


# TODO: DOC RETURN TYPE!

# TODO: migrate to abstract network topology: #54,#55
# TODO: DOC
# def start_wirefilters(mode, interface_a, interface_b = None,
#                       node_ids = None,
#                       **kwargs):
#     '''
#     Start `Wirefilter`s between the `node_ids` with the given `mode`.
#
#     Parameters
#     ----------
#     mode: str
#         See `MODE_` prefixed constants.
#     interface_a: Interface
#     interface_b: Interface, optional (default is None)
#         By default interface_b = interface_a
#     node_ids : iterable<int>
#
#     Returns
#     -------
#     dict<(int, int), (WireFilter, Interface, Interface>
#         Remembers which node ids are connected with a wirefilter.
#     '''
#     if interface_b is None:
#         interface_b = interface_a
#
#     log.info("starting wirefilters ...")
#
#     # create the tuples which shall be connected
#     tuples = create_node_indexes(mode, node_ids)
#     log.info("connections: %s", tuples)
#
#     wirefilters = OrderedDict()
#     for x, y in tuples:
#         enx, eny = EmulationNode(x, Interfaces([interface_a])), EmulationNode(y, [interface_b])
#         wirefilters[(enx.id, eny.id)] =  connect_nodes(enx, eny, interface_a, interface_b, **kwargs)
#
#     return wirefilters


###############################################
# Connection Modes
###############################################

MODE_CIRCLE = "circle"
MODE_STAR = "star"
MODE_PAIRWISE = "pairwise"
MODE_PAIRWISE_RANDOM = 'pairwise_random'
MODES = set([
    MODE_CIRCLE,
    MODE_PAIRWISE,
    MODE_PAIRWISE_RANDOM,
    MODE_STAR
])


def create_node_indexes(mode, node_ids):
    '''
    Generate a list of pairs which shall be connected to each other.
    The `mode` influences the pair calculation.

    Parameters
    ----------
    mode: str
        See `MODE_` prefixed constants
    node_ids: list<int>
        List of node ids.

    Returns
    -------
    list<tuple<int, int>>
    '''

    def rand():
        return node_ids[random.randint(0, len(node_ids) - 1)]

    def pairwise():
        return zip(node_ids, node_ids[1:])

    if mode == MODE_PAIRWISE_RANDOM:
        return zip([rand() for _ in node_ids], [rand() for _ in node_ids])
    elif mode == MODE_PAIRWISE:
        return pairwise()
    elif mode == MODE_STAR:
        return [(x, y) for x in node_ids for y in node_ids if y > x]
    elif mode == MODE_CIRCLE:
        return pairwise() + [(0, node_ids[-1])]

###############################################
###
###############################################

# TODO: UNUSED!
# def setup_network_from_dict(connections_dict):
#     '''
#     Setup the network topology by reading which nodes are connected to each other from the core config file.
#     Assume the nodes are connected on the Mesh VLAN.
#
#     Parameters
#     ----------
#     connections_dict : str
#         Path to the core xml file
#
#     Returns
#     -------
#     list<Wirefilter>, dict<int, list<int>
#         Wirefilters, Which nodes are connected to each other.
#     '''
#     connections = []
#
#     log.info("connecting nodes: %s", pformat(connections_dict))
#     for node_id in connections_dict:
#         node = EmulationNode(node_id, Interfaces.factory([Mesh]))
#         for neighbour_id in connections_dict[node_id]:
#             neighbour_node = EmulationNode(neighbour_id, Interfaces.factory([Mesh]))
#             log.info("connecting %s <-> %s", node_id, neighbour_id)
#             wf, if_a, if_b = connect_nodes(node, neighbour_node, interface_a = Interfaces.factory([Mesh])[0], start_activated = True)
#             connections.append(wf)
#
#     return connections, connections_dict
