from miniworld.service.network.NetworkConfiguratorP2P import NetworkConfiguratorP2P
from miniworld.service.network.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.singletons import singletons


class NetworkConfiguratorFactory:
    NETWORK_CONFIGURATOR_NAME_SAME_SUBNET = 'same_subnet'
    NETWORK_CONFIGURATOR_NAME_P2P = 'p2p'

    @staticmethod
    def get():
        """

        Returns
        -------
        type
            Subclass of NetworkConfigurator
        """
        if singletons.network_backend.get_network_provisioner():
            return singletons.network_backend.get_network_provisioner()

        if singletons.scenario_config.get_network_provisioner_name() == NetworkConfiguratorFactory.NETWORK_CONFIGURATOR_NAME_P2P:
            return NetworkConfiguratorP2P
        elif singletons.scenario_config.get_network_provisioner_name() == NetworkConfiguratorFactory.NETWORK_CONFIGURATOR_NAME_SAME_SUBNET:
            return NetworkConfiguratorSameSubnet

        raise ValueError('unknown provisioner {}'.format(singletons.scenario_config.get_network_provisioner_name()))
