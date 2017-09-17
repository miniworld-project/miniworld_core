from miniworld.log import get_node_logger, log
from miniworld.model.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.network.interface import Interfaces
from miniworld.model.network.interface.Interface import *

__author__ = 'Nils Schmidt'


class EmulationNodeNetworkBackendBridgedMultiDevice(EmulationNodeNetworkBackend):

    def __init__(self, network_backend_bootstrapper, node_id,
                 # network
                 interfaces=None, management_switch=False):
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
            if not isinstance(_if, HubWiFi) and not isinstance(_if, Management):
                log.debug("connections for '%s':'%s'", node_id, singletons.network_backend.get_all_connections().get(node_id))
                adjusted_interfaces.extend(type(_if) for _ in singletons.network_backend.get_all_connections()[node_id])
            else:
                adjusted_interfaces.append(type(_if))

        return Interfaces.Interfaces.factory(adjusted_interfaces)

    def nic_ipv4_config(self, emulation_node):
        pass
