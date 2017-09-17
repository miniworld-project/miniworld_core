from miniworld.Scenario import scenario_config
from miniworld.errors import NetworkBackendUnknown
from miniworld.management.network.manager.provisioner import NetworkConfiguratorP2P, NetworkConfiguratorSameSubnet
from miniworld.model.network.backends import VirtualNodeNetworkBackend

from miniworld.model.network.backends.NetworkBackendBootStrapper import NetworkBackendBootStrapper

__author__ = 'Nils Schmidt'

NETWORK_BACKENDS_VDE = "vde"
NETWORK_BACKENDS_BRIDGED = "bridged"

NETWORK_BACKENDS = {
    NETWORK_BACKENDS_VDE,
    NETWORK_BACKENDS_BRIDGED
}

# TODO: #54,#55, DOC


def get_network_backend_bootstrapper_for_string(network_backend_name):
    """

    Parameters
    ----------
    network_backend_name : str

    Returns
    -------
    NetworkBackendBootstrapper
    """

    if network_backend_name == NETWORK_BACKENDS_VDE:

        from miniworld.model.network.backends.vde import EmulationNodeVDE, QemuVDE, NetworkBackendVDE, Wirefilter, VDESwitch, CentralVDENode, ManagementNodeVDE, EmulationNodeNetworkBackend

        return NetworkBackendBootStrapper(NetworkBackendVDE.NetworkBackendVDE,
                                          EmulationNodeNetworkBackend.EmulationNodeNetworkBackendVDE,
                                          EmulationNodeVDE.EmulationNodeVDE,
                                          QemuVDE.QemuVDE,
                                          Wirefilter.Wirefilter,
                                          VDESwitch.VDESwitch,
                                          NetworkConfiguratorSameSubnet.NetworkConfiguratorSameSubnet,
                                          VirtualNodeNetworkBackend.VirtualNodeNetworkBackend,
                                          CentralVDENode.CentralVDENode,
                                          ManagementNodeVDE.ManagementNodeVDE)
    elif network_backend_name == NETWORK_BACKENDS_BRIDGED:

        from miniworld.model.network.backends.bridged.iproute2 import NetworkBackendBridged, Connection, Bridge
        from miniworld.model.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
        from miniworld.model.network.backends.bridged.iproute2.Tunnel import VLANTunnel, GreTapTunnel, VXLanTunnel

        def tunnel_factory():
            if scenario_config.is_network_backend_bridged_distributed_mode_vlan():
                return VLANTunnel
            elif scenario_config.is_network_backend_bridged_distributed_mode_gretap():
                return GreTapTunnel
            elif scenario_config.is_network_backend_bridged_distributed_mode_vxlan():
                return VXLanTunnel

        # TODO:
        if scenario_config.is_network_backend_bridged_execution_mode_iproute2():

            return _boot_strapper_backend_bridged_for_execution_mode(
                NetworkBackendBridged.NetworkBackendBridgedIproute2(),
                Connection.ConnectionIproute2(),
                Bridge.BridgeIproute2(),
                tunnel_type=tunnel_factory())

        elif scenario_config.is_network_backend_bridged_execution_mode_brctl():
            from miniworld.model.network.backends.bridged.brctl import NetworkBackendBridged, Bridge
            from miniworld.model.network.backends.bridged.iproute2 import Connection
            return _boot_strapper_backend_bridged_for_execution_mode(NetworkBackendBridged.NetworkBackendBridgedBrctl(),
                                                                     Connection.ConnectionIproute2(),
                                                                     Bridge.BridgeBrctl(),
                                                                     tunnel_type=tunnel_factory())

        elif scenario_config.is_network_backend_bridged_execution_mode_pyroute2():
            from miniworld.model.network.backends.bridged.pyroute2 import NetworkBackendBridged, Connection, Bridge
            return _boot_strapper_backend_bridged_for_execution_mode(NetworkBackendBridged.NetworkBackendBridgedPyroute2IPRoute(),
                                                                     Connection.ConnectionPyroute2IPRoute(),
                                                                     Bridge.BridgePyroute2IPRoute(),
                                                                     tunnel_type=tunnel_factory())

        else:
            raise ValueError("Execution mode for backend '%s' unknown!" % NETWORK_BACKENDS_BRIDGED)

    raise NetworkBackendUnknown("The network backend  '%s' is unknown! Available backends: %s." % (network_backend_name, ', '.join(NETWORK_BACKENDS)))


def _boot_strapper_backend_bridged_for_execution_mode(network_backend, connection, bridge, tunnel_type=None):
    """

    Parameters
    ----------
    network_backend : type
    connection : type
    bridge : type

    Returns
    -------
    NetworkBackendBootStrapper
    """
    from miniworld.model.network.backends.bridged import EmulationNodeBridged, CentralBridgeNode, ManagementNodeBridged, EmulationNodeNetworkBackendBridgedMultiDevice
    from miniworld.model.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
    from miniworld.model.network.backends.bridged import QemuTap

    # dynamic
    emulation_node_network_mixin = EmulationNodeNetworkBackend if scenario_config.is_network_backend_bridged_connection_mode_single() else EmulationNodeNetworkBackendBridgedMultiDevice.EmulationNodeNetworkBackendBridgedMultiDevice

    return NetworkBackendBootStrapper(network_backend,
                                      emulation_node_network_mixin,
                                      EmulationNodeBridged.EmulationNodeBridged,
                                      QemuTap.QemuTap,
                                      connection,
                                      bridge,
                                      NetworkConfiguratorP2P.NetworkConfiguratorP2P,
                                      VirtualNodeNetworkBackend.VirtualNodeNetworkBackend,
                                      CentralBridgeNode.CentralBridgeNode,
                                      ManagementNodeBridged.ManagementNodeBridged,
                                      tunnel_type=tunnel_type)

# TODO: #54: DOC,


def get_current_network_backend_bootstrapper():
    """
    Get a copy of the current :py:class:`.NetworkBackend`.

    Returns
    -------
    NetworkBackendBootstrapper

    """
    return get_network_backend_bootstrapper_for_string(scenario_config.get_network_backend())
