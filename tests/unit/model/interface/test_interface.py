from ipaddress import IPv4Address

from miniworld.model.interface.Interfaces import Interfaces


class TestInterface:
    def test_get_ip(self):
        ap, mesh, mgmt = Interfaces.factory_from_interface_names(['ap', 'mesh', 'management'])

        assert ap.get_ip(0) == IPv4Address('10.0.0.1')
        assert mesh.get_ip(0) == IPv4Address('10.0.1.1')
        assert mgmt.get_ip(0) == IPv4Address('172.21.0.1')
