from miniworld.model.interface import Interfaces, Interface
from miniworld.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
from miniworld.singletons import singletons

__author__ = 'Nils Schmidt'


class EmulationNodeNetworkBackendBridgedMultiDevice(EmulationNodeNetworkBackend):

    def __init__(self, network_backend_bootstrapper, node_id,
                 # network
                 interfaces=None, management_switch=False):
        self._logger = singletons.logger_factory.get_logger(self)
        interfaces = self.adjust_interfaces_to_number_of_links(node_id, interfaces)
        super(EmulationNodeNetworkBackendBridgedMultiDevice, self).__init__(network_backend_bootstrapper, node_id, interfaces=interfaces, management_switch=management_switch)

    def adjust_interfaces_to_number_of_links(self, node_id, interfaces):
        """
        For each connection, add an additional interface.

        Parameters
        ----------
        node_id
        interfaces : list<type>

        Returns
        -------
        Interfaces
        """

        adjusted_interfaces = []
        for _if in interfaces:
            if not isinstance(_if, Interface.HubWiFi) and not isinstance(_if, Interface.Management):
                self._logger.debug("connections for '%s':'%s'", node_id, singletons.network_backend.get_all_connections().get(node_id))
                adjusted_interfaces.extend(type(_if) for _ in singletons.network_backend.get_all_connections()[node_id])
            else:
                adjusted_interfaces.append(type(_if))

        return Interfaces.Interfaces.factory(adjusted_interfaces)

    def nic_ipv4_config(self, emulation_node):
        pass
