from miniworld.model import StartableObject, ResetableInterface
from miniworld.network.backends import NetworkBackendNotifications
from miniworld.singletons import singletons

__author__ = 'Nils Schmidt'


def get_superclass_dynamic():
    import miniworld.network.backends.NetworkBackendDynamic
    import miniworld.network.backends.NetworkBackendStatic
    assert singletons.scenario_config.is_network_backend_bridged_connection_mode_set()

    return miniworld.network.backends.NetworkBackendStatic.NetworkBackendStatic() if singletons.scenario_config.get_walk_model_name() == singletons.scenario_config.WALK_MODEL_NAME_CORE is not None else miniworld.network.backends.NetworkBackendDynamic.NetworkBackendDynamic()


# TODO: #82: doc code used by network backends and NetworkBackendEmulationNode!
# TODO: mark as ABC class!
class NetworkBackendDummy(StartableObject.ScenarioState,
                          ResetableInterface.ResetableInterface,
                          NetworkBackendNotifications.NetworkBackendNotifications,
                          ):
    """
    Attributes
    ----------
    network_backend_boot_strapper : NetworkBackendBootStrapper
    switches: dict<Interface, AbstractSwitch>
        One AbstractSwitch for each interface.
    """

    def __init__(self, network_backend_boot_strapper):
        StartableObject.ScenarioState.__init__(self)
        self.network_backend_bootstrapper = network_backend_boot_strapper

        self.switches = None
        self._logger = singletons.logger_factory.get_logger(self)

    #########################################
    ###
    #########################################

    def get_interface_index(self, emulation_node, interface):
        """
        Get the interface index. Assumes ascending nic naming schema like eth0, eth1, ...

        Parameters
        ----------
        emulation_node : EmulationNode
        interface : Interface

        Returns
        -------
        int
        """
        raise NotImplementedError

    def get_network_provisioner(self):
        """
        Let the network backend decide which network provisioner it needs.
        If None is returned, use the one provided in the scenario singletons.config.

        Returns
        -------
        type<NetworkConfigurator>
        """
        return

    def get_interface_filter(self):
        """
        Let the network backend choose which interfaces can be connected to each other.

        Returns
        -------
        type<InterfaceFilter>
            Return a reference to the class which shall be created.
        """
        raise NotImplementedError


def NetworkBackend():
    """
    Create the backend supertype dynamically! This is needed for different scenarios!
    """

    class NetworkBackend(get_superclass_dynamic()):
        pass

    return NetworkBackend
