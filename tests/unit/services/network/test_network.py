from unittest.mock import MagicMock

import pytest

from miniworld.model.domain.interface import Interface
from miniworld.service.emulation.interface import InterfaceService
from miniworld.service.network.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet


class TestNetworkConfiguratorSameSubnet:
    @pytest.fixture
    def service(self):
        def interface_index_fun(emulation_node, interface):
            return interface._id

        return NetworkConfiguratorSameSubnet(interface_index_fun)

    @pytest.fixture
    def interface_service(self):
        return InterfaceService()

    def test_configure_connection(self,
                                  service: NetworkConfiguratorSameSubnet,
                                  ):
        # TODO: use node domain model
        emulation_node = MagicMock()
        emulation_node._node._id = 0
        emulation_node2 = MagicMock()
        emulation_node2._node._id = 1

        interfaces = [
            Interface(_id=0, name=Interface.InterfaceType.mesh.value, nr_host_interface=0),
            Interface(_id=1, name=Interface.InterfaceType.mesh.value, nr_host_interface=1),
        ]
        emulation_node._node.interfaces = interfaces
        emulation_node2._node.interfaces = interfaces

        # configure node 1
        commands_per_node, _ = service.configure_connection(emulation_node=emulation_node)
        assert len(commands_per_node) == 1
        commands = list(commands_per_node.values())[0]
        assert commands == [
            'ifconfig eth0 10.0.0.1 netmask 255.255.0.0 up',
            'ifconfig eth1 10.1.0.1 netmask 255.255.0.0 up',
        ]

        # configure node 2
        commands_per_node, _ = service.configure_connection(emulation_node=emulation_node2)
        assert len(commands_per_node) == 1
        commands = list(commands_per_node.values())[0]
        assert commands == [
            'ifconfig eth0 10.0.0.2 netmask 255.255.0.0 up',
            'ifconfig eth1 10.1.0.2 netmask 255.255.0.0 up',
        ]
