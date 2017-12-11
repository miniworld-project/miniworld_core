import subprocess
from io import StringIO

from miniworld.model.domain.interface import Interface
from miniworld.model.domain.node import Node
from miniworld.nodes import AbstractNode
from miniworld.nodes import VirtualizationLayer
from miniworld.service.emulation.interface import InterfaceService
from miniworld.service.provisioning.CommandRunner import REPLUnexpectedResult
from miniworld.singletons import singletons
from miniworld.util import NetUtil, ConcurrencyUtil

__author__ = 'Nils Schmidt'


def get_cmd_rename_mgmt_interface():
    # TODO: #63: generic solution? works only if image has iproute2 installed :/
    CMD_RENAME_MANAGEMENT_INTERFACE = """
# name management interface
last_eth=$(ls -1 /sys/class/net/|grep {iface_prefix}|tail -n 1)
ip link set name {mgmt_iface} $last_eth
ifconfig {mgmt_iface} up
""".format(mgmt_iface=singletons.config.get_bridge_tap_name(),
           iface_prefix=singletons.scenario_config.get_network_links_nic_prefix())

    return CMD_RENAME_MANAGEMENT_INTERFACE


class EmulationService(AbstractNode):
    """ Models a node in a mesh network.

    A node consists of a QEMU instance running e.g. an OpenWRT image.
    """

    #############################################################
    # Magic and private methods
    #############################################################

    def __init__(self):
        super().__init__()
        self._interface_service = InterfaceService()
        self._logger = singletons.logger_factory.get_logger(self)

        # qemu instance, prevent cyclic import
        self.virtualization_layers = {}  # type: Dict[int, VirtualizationLayer]

    def start(self, *args, **kwargs):
        """
        Starting a node involves the following steps:

        1. Start the :py:class:`.EmulationNodeNetworkBackend.
        2. Start a :py:class:`.VirtualizationLayer` instance
        3. Update some events
        4. Give the :py:class:`.EmulationNodeNetworkBackend` a chance for some config

        Parameters
        ----------
        flo_post_boot_script: file-like-object, optional (default is None)
            Run commands from `flo_post_boot_script` on the shell after successful boot.
        """

        flo_post_boot_script = kwargs.get("flo_post_boot_script")
        node = kwargs['node']  # type: Node

        # create new virtualization layer
        self.virtualization_layers[node._id] = virtualization_layer = singletons.network_backend_bootstrapper.virtualization_layer_type(node=node)

        nlog = singletons.logger_factory.get_node_logger(node._id)
        if flo_post_boot_script is not None:
            del kwargs["flo_post_boot_script"]

        es = singletons.event_system

        # start and wait for switches
        # Ticket #82
        # self.network_backend.start_switches_blocking()
        # start qemu
        nlog.info("starting node ...")
        virtualization_layer.start(*args, **kwargs)
        nlog.info("node running ...")

        # notify EventSystem even if there are no commands
        with es.event_no_init(es.EVENT_VM_SHELL_PRE_NETWORK_COMMANDS, finish_ids=[node._id]):
            # do this immediately after the node has been started
            self.run_pre_network_shell_commands(flo_post_boot_script, node=node)

        self.after_pre_shell_commands(node=node)
        self.do_network_config_after_pre_shell_commands(node=node)

    def reset(self):
        pass

    #############################################################
    # Shell-command execution
    #############################################################

    def all_nodes_booted(self):
        self._logger.info('after_boot')
        if singletons.config.is_qemu_snapshot_boot():
            self.create_snapshots_parallel()

    def create_snapshots_parallel(self):
        self._logger.info("creating snapshots ...")
        with ConcurrencyUtil.node_start_parallel() as executor:
            res = executor.map(lambda qemu: qemu.make_snapshot(), self.virtualization_layers.values())
            # wait for evaluation!
            list(res)

    def run_pre_network_shell_commands(self, flo_post_boot_script, node: Node):
        """
        Run user commands

        Parameters
        ----------
        flo_post_boot_script
        args
        kwargs

        Returns
        -------
        """
        nlog = singletons.logger_factory.get_node_logger(node._id)
        # run post boot script in instance
        if flo_post_boot_script is not None:
            virtualization_layer = self.virtualization_layers[node._id]
            virtualization_layer.run_commands_eager(StringIO(flo_post_boot_script.read()))

        nlog.info("pre_network_shell_commands done")

    def run_post_network_shell_commands(self, emulation_node: 'EmulationService'):
        """
        Run user commands. This method is called from the :py:class:`.SimulationManager`
         after the network has been set up.
        """
        nlog = singletons.logger_factory.get_node_logger(emulation_node._node._id)
        # TODO: use node_id everywhere possible for singletons.scenario_config.*()
        # # notify EventSystem even if there are no commands
        es = singletons.event_system
        with es.event_no_init(es.EVENT_VM_SHELL_POST_NETWORK_COMMANDS, finish_ids=[emulation_node._node._id]):
            commands = singletons.scenario_config.get_all_shell_commands_post_network_start(node_id=emulation_node._node._id)
            if commands:
                virtualization_layer = self.virtualization_layers[emulation_node._node._id]
                virtualization_layer.run_commands_eager(StringIO(commands))

            nlog.info("post_network_shell_commands done")

    #############################################################
    # EmulationNode notifications
    #############################################################

    def after_pre_shell_commands(self, node: Node):
        pass

    def do_network_config_after_pre_shell_commands(self, node: Node):
        # Rename Management Interface and set ip
        if singletons.config.is_management_switch_enabled():
            virtualization_layer = self.virtualization_layers[node._id]
            virtualization_layer.run_commands_eager(StringIO(get_cmd_rename_mgmt_interface()))
            self.nic_mgmt_ipv4_config(node=node)

        self.nic_ipv4_config(node=node)

        # set NIC state up
        for _if in node.interfaces:
            tap = singletons.network_backend.get_tap_name(node._id, _if)
            # TODO: abstract NIC COMMANDS!
            cmd = "ifconfig {} up".format(tap)
            try:
                singletons.shell_helper.run_shell("host shell", cmd, prefixes=[str(node._id)])
            except subprocess.CalledProcessError as e:
                pass

    #########################################
    # Network Config
    #########################################

    def _nic_mgmt_ipv4_config(self, node: Node):
        for _if in [interface for interface in node.interfaces if interface.name == Interface.InterfaceType.management.value]:
            ip = self._interface_service.get_ip(node_id=node._id, interface=_if)
            _if.ipv4 = str(ip)
            netmask = self._interface_service.get_netmask(interface=_if)
            cmd_ip_change = NetUtil.get_ip_addr_change_cmd(singletons.config.get_bridge_tap_name(), ip, netmask)
            try:
                virtualization_layer = self.virtualization_layers[node._id]
                virtualization_layer.run_commands_eager_check_ret_val(StringIO(cmd_ip_change))
            except REPLUnexpectedResult:
                self._logger.error('could not set ip on management interface {}'.format(singletons.config.get_bridge_tap_name()))

    def nic_ipv4_config(self, node: Node):
        pass

    def nic_mgmt_ipv4_config(self, node: Node):
        self._nic_mgmt_ipv4_config(node=node)
