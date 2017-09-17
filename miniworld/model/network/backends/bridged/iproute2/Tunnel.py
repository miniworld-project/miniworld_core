# TODO:
from ordered_set import OrderedSet

from miniworld.log import log
from miniworld.model import StartableObject
from miniworld.model.network.backends.bridged.iproute2 import IPRoute2Commands
from miniworld.model.singletons.Singletons import singletons
from miniworld.util import NetworkBackendUtil

# TODO: move to base package!
GRETAP_MTU = 1458


class AbstractTunnel(StartableObject.StartableSimulationStateObject):
    """
    Attributes
    ----------
    emulation_node_x : EmulationNode
    emulation_node_y: EmulationNode
    prefix : str
    remote_ip : str
        IP address of the remote peer.
    """

    def __init__(self, emulation_node_x, emulation_node_y, remote_ip):

        super(AbstractTunnel, self).__init__()

        self.emulation_node_x = emulation_node_x
        self.emulation_node_y = emulation_node_y
        self.remote_ip = remote_ip

    def _start(self, *args, **kwargs):
        tunnel_set_group_cmd = IPRoute2Commands.get_add_interface_to_group_cmd(self.get_tunnel_name(),
                                                                               IPRoute2Commands.GROUP_TUNNELS)
        # run_shell(tunnel_set_group_cmd)

    def run_shell(self, cmd):
        singletons.shell_helper.run_shell(0, cmd, prefixes=["tunnel"])

    def add_command(self, event, cmd):
        # TODO: set id
        # tunnel devices have to be created before it can be added to the bridge
        singletons.network_backend.shell_command_executor.add_command(self.EVENT_ROOT, event, 0, cmd, self.PREFIXES)

    def get_tunnel_id(self):
        return NetworkBackendUtil.szudzik_pairing_function(self.emulation_node_x.id, self.emulation_node_y.id)

    def get_tunnel_name(self):
        raise NotImplementedError

    def get_local_emulation_node(self):
        return self.emulation_node_x if singletons.simulation_manager.is_local_node(self.emulation_node_x.id) else self.emulation_node_y


class TunnelIPRoute(AbstractTunnel):

    EVENT_ROOT = "tunnel"
    EVENT_TUNNEL_REMOVE = "tunnel_remove"
    EVENT_TUNNEL_ADD = "tunnel_add"
    EVENT_ORDER = OrderedSet([EVENT_TUNNEL_REMOVE, EVENT_TUNNEL_ADD])

    """
    Attributes
    ----------
    PREFIXES : list<str>
    """

    def __init__(self, *args, **kwargs):
        super(TunnelIPRoute, self).__init__(*args, **kwargs)
        self.PREFIXES = [TunnelIPRoute.__class__.__name__]

    def get_tunnel_name(self):
        return singletons.network_backend.get_tunnel_name(self.emulation_node_x.id, self.emulation_node_y.id)

    def reset(self):
        from miniworld.model.network.backends.bridged.iproute2 import IPRoute2Commands

        self.run_shell(IPRoute2Commands.get_link_del_cmd(self.get_tunnel_name()))

    def _shutdown(self):
        tunnel_cmd = IPRoute2Commands.get_link_del_cmd(self.get_tunnel_name())
        self.add_command(self.EVENT_TUNNEL_REMOVE, tunnel_cmd)

# TODO: set tunnel group


class GreTapTunnel(TunnelIPRoute):

    def _start(self):

        # TODO: use ShellCommandSerializer
        tunnel_cmd = IPRoute2Commands.get_gretap_tunnel_cmd(self.get_tunnel_name(), self.remote_ip, self.get_tunnel_id())

        log.info("creating gretap tunnel for %s<->%s" % (self.emulation_node_x.id, self.emulation_node_y.id))

        self.add_command(self.EVENT_TUNNEL_ADD, tunnel_cmd)

        log.info("changing NIC MTU to '%d' ... ", GRETAP_MTU)
        self.get_local_emulation_node().virtualization_layer.set_link_mtus(mtu=GRETAP_MTU)

        # set tunnel dev group
        super(GreTapTunnel, self)._start()

# TODO:


class VLANTunnel(TunnelIPRoute):
    VLAN_BITS = 12

    # # TODO: what are the maximum number of interfaces/hosts for the vlan solution?
    # # NOTE: 0,4095 are reserved VLAN ids
    # if tunnel_id  >= 2**VLAN_BITS - 1 or tunnel_id == 0:
    #     raise ValueError("'%s' is not a valid VLAN id!" % tunnel_id)

    def _start(self):
        self.add_command(self.EVENT_TUNNEL_ADD,
                         "ip link add link {net_dev} name {tunnel_name} type vlan id {vlan_id}".format(
                             net_dev='eth0', tunnel_name=self.get_tunnel_name(), vlan_id=self.get_tunnel_id())
                         )
        # set tunnel dev group
        super(VLANTunnel, self)._start()

# TODO:


class VXLanTunnel(TunnelIPRoute):
    """ ip link add name vxlan0 type vxlan id 42 dev eth0 group 239.0.0.1 dstport 4789 """

    def _start(self):
        self.add_command(self.EVENT_TUNNEL_ADD,
                         # TODO: do we need to check for a free mcast group??
                         "ip link add name {tunnel_name} type vxlan id {vlan_id} group 239.0.0.1 dstport 4789".format(
                             tunnel_name=self.get_tunnel_name(), vlan_id=self.get_tunnel_id())
                         )
        # set tunnel dev group
        super(VXLanTunnel, self)._start()
