from collections import defaultdict
from functools import partial

import os
import pytest
import subprocess
from miniworld import Scenario
from tests.conftest import create_runner


@pytest.fixture(scope='session')
def runner(tmpdir_factory, image_path, request, config_path):
    runner = create_runner(tmpdir_factory, request, config_path)

    with runner() as r:
        r.connection_modes = set()
        yield r


@pytest.fixture
def snapshot_runner(runner):
    yield runner
    runner.stop(hard=False)


# TODO: theoretically we need to manually check network connectivity since network checking code may not run at all :/
def _create_scenarios(connection_mode):
    for execution_mode in Scenario.ScenarioConfig.EXECUTION_MODES:
        def fun(connection_mode, execution_mode, image_path, request, core_topologies_dir):
            return {
                "scenario": "acceptance_network_switching",
                "walk_model": {
                    "name": "core"
                },
                "cnt_nodes": 5,
                "provisioning": {
                    "image": image_path,
                    "regex_shell_prompt": "root@OpenWrt:/#",
                    "shell": {
                        "pre_network_start": {
                            "shell_cmds": [
                                # we need to wait for the NICs to be up
                                "until ifconfig eth0; do echo -n . && sleep 1; done",
                                "until ifconfig br-lan ; do echo -n . && sleep 1; done",
                                "ifconfig eth0 down",
                                "ifconfig br-lan down",
                                "brctl delif br-lan eth0",
                                "ifconfig eth0 up",
                                "ifconfig -a",
                                "brctl show"
                            ]
                        }
                    }
                },
                "network": {
                    "backend": {
                        "name": "bridged",
                        "connection_mode": connection_mode,
                        "execution_mode": {
                            "name": execution_mode,
                        }
                    },
                    "links": {
                        "model": "miniworld.model.network.linkqualitymodels.LinkQualityModelRange.LinkQualityModelRange"
                    },
                    "core": {
                        "topologies": [
                            [0, os.path.join(core_topologies_dir, "chain5.xml")],
                            [0, os.path.join(core_topologies_dir, "clique5.xml")],
                            [0, os.path.join(core_topologies_dir, "cycle5.xml")],
                            [0, os.path.join(core_topologies_dir, "star5.xml")],
                            [0, os.path.join(core_topologies_dir, "wheel5.xml")],
                        ],
                        "mode": "lan"
                    }
                }
            }

        # we need to inject the environment into the function
        yield partial(fun, connection_mode, execution_mode), '{}_{}'.format(connection_mode, execution_mode)


@pytest.mark.parametrize('scenario_fun',
                         **dict(zip(['argvalues', 'ids'], zip(*_create_scenarios(Scenario.CONNECTION_MODE_SINGLE)))))
def test_network_switching_bridged_backends_single(scenario_fun, snapshot_runner, image_path, request, core_topologies_dir):
    _test_network_switch_bridged_backends(core_topologies_dir, image_path, request, snapshot_runner, scenario_fun)


@pytest.mark.parametrize('scenario_fun',
                         **dict(zip(['argvalues', 'ids'], zip(*_create_scenarios(Scenario.CONNECTION_MODE_MULTI)))))
def test_network_switching_bridged_backends_multi(scenario_fun, snapshot_runner, image_path, request, core_topologies_dir):
    _test_network_switch_bridged_backends(core_topologies_dir, image_path, request, snapshot_runner, scenario_fun)


def _test_network_switch_bridged_backends(core_topologies_dir, image_path, request, runner, scenario_fun):
    scenario = scenario_fun(image_path, request, core_topologies_dir)
    connection_mode = scenario['network']['backend']['connection_mode']
    if not connection_mode in runner.connection_modes:
        force_snapshot_boot = False
        runner.connection_modes.add(connection_mode)
    else:
        force_snapshot_boot = True

    brctl_output_before = subprocess.check_call(['brctl', 'show'])
    ebtables_before = subprocess.check_call(['ebtables', '-L'])
    runner.start_scenario(scenario, force_snapshot_boot=force_snapshot_boot)
    for i in range(len(scenario['network']['core']['topologies'])):
        runner.step()
    brctl_output_after = subprocess.check_call(['brctl', 'show'])
    ebtables_after = subprocess.check_call(['ebtables', '-L'])
    # check cleanup done correctly
    assert brctl_output_before == brctl_output_after, 'network backend cleanup not working'
    assert ebtables_before == ebtables_after, 'network backend cleanup not working'
