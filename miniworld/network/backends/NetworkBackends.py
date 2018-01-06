from miniworld.errors import NetworkBackendUnknown
from miniworld.network.backends.NetworkBackendBootStrapper import NetworkBackendBootStrapper


from miniworld.service.network import NetworkConfiguratorSameSubnet
from miniworld.singletons import singletons

__author__ = 'Nils Schmidt'

NETWORK_BACKENDS_BRIDGED = "bridged"

NETWORK_BACKENDS = {
    NETWORK_BACKENDS_BRIDGED
}


class NetworkBackendBootstrapperFactory:
    @staticmethod
    def get():
        """
        Get a copy of the current :py:class:`.NetworkBackend`.

        Returns
        -------
        NetworkBackendBootstrapper

        """
        return NetworkBackendBootstrapperFactory.get_network_backend_bootstrapper_for_string(
            singletons.scenario_config.get_network_backend())

    @staticmethod
    def get_network_backend_bootstrapper_for_string(network_backend_name):
        """

        Parameters
        ----------
        network_backend_name : str

        Returns
        -------
        NetworkBackendBootstrapper
        """

        if network_backend_name == NETWORK_BACKENDS_BRIDGED:

            from miniworld.network.backends.bridged.iproute2 import Bridge
            from miniworld.network.backends.bridged.iproute2 import Connection
            from miniworld.network.backends.bridged.iproute2 import NetworkBackendBridged
            from miniworld.network.backends.bridged.iproute2.Tunnel import VLANTunnel, GreTapTunnel, VXLanTunnel

            def tunnel_factory():
                if singletons.scenario_config.is_network_backend_bridged_distributed_mode_vlan():
                    return VLANTunnel
                elif singletons.scenario_config.is_network_backend_bridged_distributed_mode_gretap():
                    return GreTapTunnel
                elif singletons.scenario_config.is_network_backend_bridged_distributed_mode_vxlan():
                    return VXLanTunnel

            # TODO:
            if singletons.scenario_config.is_network_backend_bridged_execution_mode_iproute2():

                return NetworkBackendBootstrapperFactory._boot_strapper_backend_bridged_for_execution_mode(
                    NetworkBackendBridged.NetworkBackendBridgedIproute2(),
                    Connection.ConnectionIproute2(),
                    Bridge.BridgeIproute2(),
                    tunnel_type=tunnel_factory())

            elif singletons.scenario_config.is_network_backend_bridged_execution_mode_brctl():
                from miniworld.network.backends.bridged.brctl import NetworkBackendBridged
                from miniworld.network.backends.bridged.brctl import Bridge
                from miniworld.network.backends.bridged.iproute2 import Connection
                return NetworkBackendBootstrapperFactory._boot_strapper_backend_bridged_for_execution_mode(
                    NetworkBackendBridged.NetworkBackendBridgedBrctl(),
                    Connection.ConnectionIproute2(),
                    Bridge.BridgeBrctl(),
                    tunnel_type=tunnel_factory())

            elif singletons.scenario_config.is_network_backend_bridged_execution_mode_pyroute2():
                from miniworld.network.backends.bridged.pyroute2 import Connection
                from miniworld.network.backends.bridged.pyroute2 import Bridge
                from miniworld.network.backends.bridged.pyroute2 import NetworkBackendBridged
                return NetworkBackendBootstrapperFactory._boot_strapper_backend_bridged_for_execution_mode(
                    NetworkBackendBridged.NetworkBackendBridgedPyroute2IPRoute(),
                    Connection.ConnectionPyroute2IPRoute(),
                    Bridge.BridgePyroute2IPRoute(),
                    tunnel_type=tunnel_factory())

            else:
                raise ValueError("Execution mode for backend '%s' unknown!" % NETWORK_BACKENDS_BRIDGED)

        raise NetworkBackendUnknown("The network backend  '%s' is unknown! Available backends: %s." % (
            network_backend_name, ', '.join(NETWORK_BACKENDS)))

    @staticmethod
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
        from miniworld.network.backends.bridged import ManagementNodeBridged
        from miniworld.network.backends.bridged import CentralBridgeNode
        from miniworld.nodes.EmulationService import EmulationService
        from miniworld.nodes.qemu import Qemu

        return NetworkBackendBootStrapper(network_backend,
                                          EmulationService,
                                          Qemu.Qemu,
                                          connection,
                                          bridge,
                                          NetworkConfiguratorSameSubnet.NetworkConfiguratorSameSubnet,
                                          CentralBridgeNode.CentralBridgeNode,
                                          ManagementNodeBridged.ManagementNodeBridged,
                                          tunnel_type=tunnel_type)
