from functools import total_ordering

from miniworld import singletons
from miniworld.Config import config
from miniworld.Scenario import scenario_config
from miniworld.model import StartableObject


__author__ = 'Nils Schmidt'
from io import StringIO

from miniworld.log import get_node_logger
from miniworld.model.ShellCmdWrapper import ShellCmdWrapper

# TODO: REMOVE
# CMD_TEMPLATE_DISABLE_IPTABLES = """
# iptables -F
# iptables -X
# iptables -t nat -F
# iptables -t nat -X
# iptables -t mangle -F
# iptables -t mangle -X
# iptables -P INPUT ACCEPT
# iptables -P FORWARD ACCEPT
# iptables -P OUTPUT ACCEPT
# """


# TODO: #54,#55: adjust doc
@total_ordering
class EmulationNode(StartableObject.StartableSimulationStateObject, ShellCmdWrapper):
    ''' Models a node in a mesh network.

    A node consists of a QEMU instance running e.g. an OpenWRT image.
    The nodes are connected via a VDE Switch, which are plugged together using a cable, a wirefilter.

    Attributes
    ----------
    nlog
        Specific node logger object.
    id: int
        ID of the node.
    virtualization_layer : VirtulizationLayer
        The node within a specific virtualization layer.
    network_mixin : EmulationNodeNetworkBackend
    network_backend_bootstrapper : NetworkBackendBootStrapper
    network_mixin : NetworkMixin, optional (default is taken :py:class:`.NetworkBackendBootStrapper`
    '''


    #############################################################
    ### Factory stuff
    #############################################################

    @staticmethod
    def factory(id):
        from miniworld.model.network.backends import NetworkBackends
        from miniworld.model.network.interface.Interfaces import Interfaces

        interfaces_str = scenario_config.get_interfaces(node_id=id)
        interfaces = Interfaces.factory_from_interface_names(interfaces_str)

        network_backend_name = scenario_config.get_network_backend()

        network_backend_bootstrapper = NetworkBackends.get_network_backend_bootstrapper_for_string(network_backend_name)
        return EmulationNode(id, network_backend_bootstrapper, interfaces)

    #############################################################
    ### Magic and private methods
    #############################################################

    def __init__(self, node_id, network_backend_bootstrapper, interfaces, network_mixin=None):
        StartableObject.StartableSimulationStateObject.__init__(self)

        self.network_backend_bootstrapper = network_backend_bootstrapper

        if network_mixin is None:
            network_mixin_type = network_backend_bootstrapper.emulation_node_network_backend_type
            self.network_mixin = network_mixin_type(network_backend_bootstrapper, node_id, interfaces=interfaces, management_switch=config.is_management_switch_enabled())
        else:
            self.network_mixin = network_mixin

        # TODO: keep or remove?
        self.interfaces = interfaces

        # node id
        self.id = node_id
        if not isinstance(self.id, int):
            raise ValueError('int required')

        # create extra node logger
        self.nlog = get_node_logger(node_id)

        # qemu instance, prevent cyclic import
        self.virtualization_layer = network_backend_bootstrapper.virtualization_layer_type(node_id, self)

        self.name = None

    @property
    def name(self):
        return self._name or str(self.id)

    @name.setter
    def name(self, name):
        self._name = name

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.id < other.id

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)
        #return '%s(%s, %s)' % (self.__class__.__name__, self.id, self.network_mixin)

    def __hash__(self):
        return hash(self.name)

    # TODO: adjust DOC
    def _start(self, *args, **kwargs):
        '''
        Starting a node involves the following steps:

        1. Start the :py:class:`.EmulationNodeNetworkBackend.
        2. Start a :py:class:`.VirtualizationLayer` instance
        3. Update some events
        4. Give the :py:class:`.EmulationNodeNetworkBackend` a chance for some config

        Parameters
        ----------
        flo_post_boot_script: file-like-object, optional (default is None)
            Run commands from `flo_post_boot_script` on the shell after successful boot.
        '''

        flo_post_boot_script = kwargs.get("flo_post_boot_script")
        if flo_post_boot_script is not None:
            del kwargs["flo_post_boot_script"]

        self.network_mixin.start()

        es = singletons.event_system

        # start and wait for switches
        # Ticket #82
        # self.network_backend.start_switches_blocking()
        # start qemu
        self.nlog.info("starting node ...")
        self.virtualization_layer.start(*args, **kwargs)
        self.nlog.info("node running ...")

        # notify EventSystem even if there are no commands
        with es.event_no_init(es.EVENT_VM_SHELL_PRE_NETWORK_COMMANDS, finish_ids=[self.id]) as ev:
            # do this immediately after the node has been started
            self.run_pre_network_shell_commands(flo_post_boot_script)

        self.after_pre_shell_commands()
        self.do_network_config_after_pre_shell_commands()

    def reset(self):
        pass

    #############################################################
    ### Shell-command execution
    #############################################################

    # TODO: #54,#55: adjust doc
    def run_pre_network_shell_commands(self, flo_post_boot_script, *args, **kwargs):
        '''
        Run user commands

        Parameters
        ----------
        flo_post_boot_script
        args
        kwargs

        Returns
        -------
        '''

        # run post boot script in instance
        if flo_post_boot_script is not None:
            self.virtualization_layer.run_commands_eager(StringIO(flo_post_boot_script.read()))

        self.nlog.info("pre_network_shell_commands done")

    # TODO: #54,#55: adjust doc
    def run_post_network_shell_commands(self, *args, **kwargs):
        '''
        Run user commands. This method is called from the :py:class:`.SimulationManager`
         after the network has been set up.
        '''
        # TODO: use node_id everywhere possible for scenario_config.*()
        # # notify EventSystem even if there are no commands
        es = singletons.event_system
        with es.event_no_init(es.EVENT_VM_SHELL_POST_NETWORK_COMMANDS, finish_ids=[self.id]) as ev:
            commands = scenario_config.get_all_shell_commands_post_network_start(node_id = self.id)
            if commands:
                self.virtualization_layer.run_commands_eager(StringIO(commands))

            self.nlog.info("post_network_shell_commands done")

    #############################################################
    ### Notify NetworkBackend
    #############################################################

    # TODO: create interface
    # TODO: REMOVE VLAN PARAM?
    def after_pre_shell_commands(self):
        self.network_mixin.after_pre_shell_commands(self, config.is_vlan_enabled())

    def do_network_config_after_pre_shell_commands(self):
        self.network_mixin.do_network_config_after_pre_shell_commands(self)

