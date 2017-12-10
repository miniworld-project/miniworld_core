from miniworld.service.network.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.singletons import singletons


class NetworkConfiguratorFactory:
    NETWORK_CONFIGURATOR_NAME_SAME_SUBNET = 'same_subnet'

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

        if singletons.scenario_config.get_network_provisioner_name() == NetworkConfiguratorFactory.NETWORK_CONFIGURATOR_NAME_SAME_SUBNET:
            return NetworkConfiguratorSameSubnet

        raise ValueError('unknown provisioner {}'.format(singletons.scenario_config.get_network_provisioner_name()))
