from typing import List

from miniworld.model.domain.interface import Interface
from miniworld.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend
from miniworld.service.emulation.interface import InterfaceService
from miniworld.singletons import singletons

__author__ = 'Nils Schmidt'


class EmulationNodeNetworkBackendBridgedMultiDevice(EmulationNodeNetworkBackend):
    def __init__(self, network_backend_bootstrapper, node_id,
                 # network
                 interfaces=None, management_switch=False):
        self._logger = singletons.logger_factory.get_logger(self)
        self._interface_service = InterfaceService()
        interfaces = self.adjust_interfaces_to_number_of_links(node_id, interfaces)
        super(EmulationNodeNetworkBackendBridgedMultiDevice, self).__init__(network_backend_bootstrapper, node_id, interfaces=interfaces, management_switch=management_switch)

    def adjust_interfaces_to_number_of_links(self, node_id: int, interfaces: List[Interface]) -> List[Interface]:
        """
        For each connection, add an additional interface of the same type.
        """
        interface_types = []  # type: List[Interface.InterfaceType]
        for _if in interfaces:
            if self._interface_service.filter_normal_interfaces([_if]):
                self._logger.debug("connections for '%s':'%s'", node_id, singletons.network_backend.get_all_connections().get(node_id))
                interface_types.extend(Interface.InterfaceType(_if.name) for _ in singletons.network_backend.get_all_connections()[node_id])
            else:
                interface_types.append(Interface.InterfaceType(_if.name))

        return self._interface_service.factory(interface_types)

    def nic_ipv4_config(self, emulation_node):
        pass
