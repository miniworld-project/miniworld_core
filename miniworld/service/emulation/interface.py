import ipaddress
from collections import defaultdict
from ipaddress import IPv4Network
from typing import Union, List, Dict, Iterable

from miniworld.model.domain.interface import Interface
from miniworld.util import NetUtil


# TODO: use domain model if EmulationNode is a POPO object
class InterfaceService:
    @staticmethod
    def factory(interface_types: List[Union[str, Interface.InterfaceType]]) -> List[Interface]:
        """
        Factory method to create the network interfaces.
        The factory takes care of counting interfaces of the same kind.
        This count+1 is passed to the :py:class:`.Interface` class (needed to differentiate between e.g. two `ap` interfaces)
        """
        # count created instances
        counter = defaultdict(lambda: 0)
        interfaces = []

        for interface_type in interface_types:
            if isinstance(interface_type, str):
                interface_type = Interface.InterfaceType(interface_type)
            assert isinstance(interface_type, Interface.InterfaceType)

            # create interface with current count
            interface = Interface()
            interface.name = interface_type.value
            interface.nr_host_interface = counter[interface.name]
            interfaces.append(interface)
            # increment counter
            counter[interface.name] += 1

        return interfaces

    #########################################################
    # IP Provisioning
    #########################################################

    # TODO: add caching ?
    @property
    def subnets(self) -> Dict[Interface.InterfaceType, IPv4Network]:
        # TODO: make subnet configurable via scenario config!
        subnets = NetUtil.get_slash_x(ipaddress.ip_network(u"10.0.0.0/8").subnets(), 24)
        # for each interface type create an extra subnet
        subnets = dict(zip(Interface.InterfaceType, subnets))
        subnets[Interface.InterfaceType.management] = ipaddress.ip_network(u"172.21.0.0/16")
        return subnets

    def get_ip_network(self, interface: Interface) -> ipaddress._BaseNetwork:
        return self.subnets[Interface.InterfaceType(interface.name)]

    def get_ip(self, node_id: int, interface: Interface) -> ipaddress._BaseAddress:
        """
        Get the ip for the `node_id`.
        """
        return self.get_ip_network(interface=interface)[node_id + 1]

    def get_ip_pred(self, node_id: int, interface: Interface) -> ipaddress._BaseAddress:
        return self.get_ip(node_id=node_id - 1, interface=interface)

    def get_ip_suc(self, node_id: int, interface: Interface) -> ipaddress._BaseAddress:
        return self.get_ip(node_id=node_id + 1, interface=interface)

    def get_last_ip(self, interface: Interface) -> ipaddress._BaseAddress:
        return self.get_ip_network(interface=interface)[-2]

    @staticmethod
    def get_mac(node_id: int, interface: Interface) -> str:
        """
        Get the mac address for the `node_id` and `interface`.
        """
        idx = [e.value for e in Interface.InterfaceType].index(interface.name)
        nc = '%02x' % idx
        nr_iface = '%02x' % interface.nr_host_interface
        node_id = '%08x' % node_id

        return '%s:%s:%s:%s:%s:%s' % (nc, nr_iface, node_id[0:2], node_id[2:4], node_id[4:6], node_id[6:8])

    def get_network_address(self, interface: Interface) -> ipaddress._BaseNetwork:
        """ Get the network ip """
        return self.get_ip_network(interface)

    def get_netmask(self, interface: Interface) -> ipaddress._BaseAddress:
        """ Get the netmask """
        return self.get_ip_network(interface=interface).netmask

    def get_template_dict(self, node_id: int, interface: Interface, *args, **kwargs):

        def f(s):
            return s % interface.name

        return {
            f("ipv4_addr_%s_pred"): str(self.get_ip_pred(node_id=node_id, interface=interface)),
            f("ipv4_addr_%s_suc"): str(self.get_ip_suc(node_id=node_id, interface=interface)),
            f("ipv4_addr_%s"): str(self.get_ip(node_id=node_id, interface=interface)),
            f("ipv4_network_%s"): str(self.get_network_address(interface=interface)),
            f("ipv4_netmask_%s"): str(self.get_netmask(interface=interface)),
        }

    @staticmethod
    def filter_normal_interfaces(interfaces: Iterable[Interface]) -> List[Interface]:
        return [interface for interface in interfaces if Interface.InterfaceType(interface.name) in Interface.INTERFACE_TYPE_NORMAL]
