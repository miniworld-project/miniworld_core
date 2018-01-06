import ipaddress

import pytest

from miniworld.model.domain.interface import Interface
from miniworld.service.emulation.interface import InterfaceService


class TestInterfaceService:
    @pytest.fixture
    def service(self):
        return InterfaceService()

    @pytest.fixture
    def interface(self, service):
        return service.factory([Interface.InterfaceType.mesh])[0]

    @pytest.mark.parametrize('interfaces', ([Interface.InterfaceType.mesh, Interface.InterfaceType.mesh], ['mesh', 'mesh']))
    def test_factory(self, service: InterfaceService, interfaces):
        interfaces = service.factory(interfaces)
        assert len(interfaces) == 2
        for idx in range(2):
            assert interfaces[idx].name == Interface.InterfaceType.mesh.value
            # check that `nr_host_interface` gets incremented
            assert interfaces[idx].nr_host_interface == idx

    def test_subnets(self, service):
        """ Check that each interface type got the correct subnet assigned. """
        subnets = service.subnets
        for idx, interface_type in enumerate(Interface.InterfaceType):
            subnet = subnets[interface_type]
            if interface_type == Interface.InterfaceType.management:
                assert str(subnet) == '172.21.0.0/16'
            else:
                assert str(subnet) == '10.0.{idx}.0/24'.format(idx=idx)

    def test_get_ip_network(self, service: InterfaceService, interface: Interface):
        assert service.get_ip_network(interface=interface) == ipaddress.ip_network('10.0.0.0/24')

    def test_get_ip(self, service: InterfaceService, interface: Interface):
        assert service.get_ip(node_id=0, interface=interface) == ipaddress.ip_address('10.0.0.1')
        assert service.get_ip_suc(node_id=0, interface=interface) == ipaddress.ip_address('10.0.0.2')
        assert service.get_ip_pred(node_id=0, interface=interface) == ipaddress.ip_address('10.0.0.0')  # network address

    def test_get_network(self, service: InterfaceService, interface: Interface):
        assert service.get_network_address(interface=interface) == ipaddress.ip_network('10.0.0.0/24')

    def test_get_netmask(self, service: InterfaceService, interface: Interface):
        assert service.get_netmask(interface=interface) == ipaddress.ip_address('255.255.255.0')

    def test_get_mac(self, service: InterfaceService, interface: Interface):
        assert service.get_mac(node_id=0, interface=interface) == '00:00:00:00:00:00'

    def test_get_template_dict(self, service: InterfaceService, interface: Interface):
        res = service.get_template_dict(node_id=0, interface=interface)
        assert res == {
            'ipv4_addr_mesh_pred': '10.0.0.0',
            'ipv4_addr_mesh_suc': '10.0.0.2',
            'ipv4_addr_mesh': '10.0.0.1',
            'ipv4_network_mesh': '10.0.0.0/24',
            'ipv4_netmask_mesh': '255.255.255.0',
        }

    def test_filter_normal_interfaces(self, service: InterfaceService):
        interfaces = service.factory([Interface.InterfaceType.mesh, Interface.InterfaceType.management, Interface.InterfaceType.hub])
        interfaces = service.filter_normal_interfaces(interfaces)
        assert len(interfaces) == 1
        assert interfaces[0].name == Interface.InterfaceType.mesh.value
