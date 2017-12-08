import functools
from copy import deepcopy
from unittest.mock import MagicMock, Mock

import pytest

from miniworld.impairment.ImpairmentModel import ImpairmentModel
from miniworld.mobility.DistanceMatrix import DistanceMatrix
from miniworld.service.emulation.EmulationManager import EmulationManager
from miniworld.service.emulation.interface import InterfaceService
from miniworld.singletons import singletons


@functools.total_ordering
class EmulationNode(Mock):
    id = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = EmulationNode.id
        EmulationNode.id += 1
        self.network_mixin = MagicMock()
        self.network_mixin.interfaces = InterfaceService.factory(['mesh'])

    def __eq__(self, other):
        return self._id == other._id

    def __lt__(self, other):
        return self._id < other._id

    def __hash__(self):
        return hash(self._id)

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
    dm.set_distance(x=0, y=1, distance=10)
    dm.set_distance(x=1, y=2, distance=30)
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

    def test_scenario_hash_changes(self, emulation_manager, scenario_config):
        """ Test that the scenario hash changes. This is necessary for the QEMU snapshot boot mode"""
        emulation_manager._start = Mock()

        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)
        emulation_manager.abort()

        # change scenario config
        scenario_config = deepcopy(scenario_config)
        scenario_config['foo'] = 'bar'
        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)

        assert emulation_manager.scenario_changed

    def test_scenario_hash_does_not_change(self, emulation_manager, scenario_config):
        """ Test that the scenario hash does not change for the same scenario_config """
        emulation_manager._start = Mock()

        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)
        emulation_manager.abort()

        # change scenario config
        scenario_config = deepcopy(scenario_config)
        scenario_config['foo'] = 'bar'
        emulation_manager.start(scenario_config=scenario_config, auto_stepping=False)

        assert emulation_manager.scenario_changed

    # TODO: test with distance matrix from MD
    # TODO: "ip link set dev" commands are in bridge group of ShellCommandExecutor, but should be in connection group instead, bridge.add_if(tap_x, if_up=True) adds the command to the bridge group. brctl backend
    def test_step(self, emulation_manager, scenario_config, distance_matrix, monkeypatch):
        mock = MagicMock(side_effect=lambda _: _)
        monkeypatch.setattr('miniworld.service.persistence.interfaces.NodePersistenceService.add', mock)
        # required by to monkeypatch network_backend_bootstrapper
        singletons.scenario_config.data = scenario_config

        # mock Qemu and ManagementNode type
        network_backend_bootstrapper = singletons.network_backend_bootstrapper
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
        emulation_manager.nodes_id_mapping = {0: EmulationNode(), 1: EmulationNode(), 2: EmulationNode()}
        singletons.scenario_config.is_network_links_auto_ipv4 = MagicMock(return_value=False)
        singletons.network_manager.net_configurator = MagicMock()

        emulation_manager.step(1, distance_matrix=distance_matrix)
