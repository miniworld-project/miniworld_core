import functools
from unittest.mock import MagicMock, Mock, call

import pytest

from miniworld.impairment.ImpairmentModel import ImpairmentModel
from miniworld.mobility.DistanceMatrix import DistanceMatrix
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.service.emulation.EmulationManager import EmulationManager
from miniworld.singletons import singletons


@functools.total_ordering
class EmulationNode(Mock):
    id = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = EmulationNode.id
        EmulationNode.id += 1
        self.network_mixin = MagicMock()
        self.network_mixin.interfaces = Interfaces.factory_from_interface_names(['mesh'])

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return 0


@pytest.fixture
def scenario_config():
    return {
        "provisioning": {
            "image": "some_image_path"
        },
    }


@pytest.fixture
def emulation_manager():
    return EmulationManager()


@pytest.fixture
def distance_matrix():
    dm = DistanceMatrix.factory()()
    dm.set_distance(x=1, y=2, distance=10)
    dm.set_distance(x=2, y=3, distance=30)
    return dm


class TestEmulationManager:
    def test_instance(self, emulation_manager):
        assert not emulation_manager.scenario_changed
        assert not emulation_manager.running
        assert emulation_manager.run_loop is None
        assert emulation_manager.current_step == 0
        assert emulation_manager.movement_director is None
        assert emulation_manager.network_backend is None
        assert emulation_manager.auto_stepping is None
        assert emulation_manager.impairment is None

        assert isinstance(emulation_manager.distance_matrix, DistanceMatrix)
        assert isinstance(emulation_manager.distance_matrix_hubwifi, DistanceMatrix)

    # TODO: parametrize with different scenario configs
    def test_run(self, emulation_manager, scenario_config):
        # mock Qemu and ManagementNode type
        singletons.network_backend_bootstrapper_factory = MagicMock()
        singletons.network_backend_bootstrapper_factory.get.return_value = MagicMock()

        # we do not want to execute shell commands
        singletons.shell_helper = MagicMock()
        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)

        assert emulation_manager.running
        assert isinstance(emulation_manager.impairment, ImpairmentModel)

    # TODO: test with distance matrix from MD
    # TODO: "ip link set dev" commands are in bridge group of ShellCommandExecutor, but should be in connection group instead, bridge.add_if(tap_x, if_up=True) adds the command to the bridge group. brctl backend
    def test_step(self, emulation_manager, scenario_config, distance_matrix):
        # required by to monkeypatch network_backend_bootstrapper
        singletons.scenario_config.data = scenario_config

        # mock Qemu and ManagementNode type
        network_backend_bootstrapper = singletons.network_backend_bootstrapper_factory.get()
        network_backend_bootstrapper.virtualization_layer_type = MagicMock()
        network_backend_bootstrapper.management_node_type = MagicMock()
        singletons.network_backend_bootstrapper_factory = MagicMock()
        singletons.network_backend_bootstrapper_factory.get.return_value = network_backend_bootstrapper

        emulation_manager.movement_director = MagicMock()
        emulation_manager.is_movement_director_enabled = MagicMock(return_value=True)

        # we do not want to execute shell commands
        singletons.shell_helper = MagicMock()

        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)

        # 2 nodes
        emulation_manager.nodes_id_mapping = {1: EmulationNode(), 2: EmulationNode(), 3: EmulationNode()}
        singletons.scenario_config.is_network_links_auto_ipv4 = MagicMock(return_value=False)
        singletons.network_manager.net_configurator = MagicMock()

        emulation_manager.step(1, distance_matrix=distance_matrix)
        # pin network setup commands
        assert singletons.shell_helper.method_calls == [
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic --atomic-init'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic --atomic-commit'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic --atomic-save'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic -N wifi1 -P DROP'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic -A FORWARD --logical-in wifi1 -j wifi1'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic -I wifi1 -i tap_00000_1 -o tap_00001_1 -j mark --set-mark 1 --mark-target ACCEPT; ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic -I wifi1 -i tap_00001_1 -o tap_00000_1 -j mark --set-mark 1 --mark-target ACCEPT'",
                           ('ebtables',)),
            call.run_shell('type',
                           "sh -c 'ebtables --concurrent --atomic-file /tmp/MiniWorld/ebtables_atommic --atomic-commit'",
                           ('ebtables',)),
            call.run_shell_with_input('ip -d -batch -',
                                      'link add name wifi1 type bridge\nlink set dev wifi1 type bridge ageing_time 0\nlink set dev tap_00000_1 master wifi1\nlink set dev tap_00000_1 up\nlink set dev wifi1 up\nlink set dev tap_00001_1 master wifi1\nlink set dev tap_00001_1 up'),
            call.run_shell_with_input('tc -d -batch -', '')]
