import os
import shlex
import subprocess
from functools import partial

import pytest
from typing import Dict, List, Iterable

from miniworld.config import Scenario
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
def test_network_switching_bridged_backends_single(scenario_fun, snapshot_runner, image_path, request,
                                                   core_topologies_dir, topologies):
    def check_topology(topology: Dict[int, Iterable[int]]):
        for x, peers in topology.items():
            for y in peers:
                check_connection(x, y)

            for i in range(scenario['cnt_nodes']):
                # exclude allowed connections and only ping based on upper-triangular matrix
                if i in peers or x >= i:
                    continue
                # check that we can not ping other nodes
                with pytest.raises(subprocess.CalledProcessError, message='{}->{} should not be reachable'.format(x, i)):
                    check_connection(x, i)

    def check_connection(x: int, y: int):
        cmd = 'exec -v --node-id {x} "ping -c 1 10.0.0.{y}"'.format(x=x, y=y + 1)
        snapshot_runner.run_mwcli_command(shlex.split(cmd))

    scenario = scenario_fun(image_path, request, core_topologies_dir)
    connection_mode = scenario['network']['backend']['connection_mode']
    if connection_mode not in snapshot_runner.connection_modes:
        force_snapshot_boot = False
        snapshot_runner.connection_modes.add(connection_mode)
    else:
        force_snapshot_boot = True

    brctl_output_before = subprocess.check_call(['brctl', 'show'])
    ebtables_before = subprocess.check_call(['ebtables', '-L'])
    snapshot_runner.start_scenario(scenario, force_snapshot_boot=force_snapshot_boot)
    for i in range(len(scenario['network']['core']['topologies'])):
        snapshot_runner.step()
        check_topology(topologies[i])
    brctl_output_after = subprocess.check_call(['brctl', 'show'])
    ebtables_after = subprocess.check_call(['ebtables', '-L'])
    # check cleanup done correctly
    assert brctl_output_before == brctl_output_after, 'network backend cleanup not working'
    assert ebtables_before == ebtables_after, 'network backend cleanup not working'


@pytest.mark.parametrize('scenario_fun',
                         **dict(zip(['argvalues', 'ids'], zip(*_create_scenarios(Scenario.CONNECTION_MODE_MULTI)))))
def test_network_switching_bridged_backends_multi(scenario_fun, snapshot_runner, image_path, request,
                                                  core_topologies_dir):
    _test_network_switch_bridged_backends(core_topologies_dir, image_path, request, snapshot_runner, scenario_fun)


@pytest.fixture
def topologies() -> List[Dict[int, Iterable[int]]]:
    return [
        {0: {1}, 1: {2}, 2: {3}, 3: {4}},
        {0: {1, 2, 3, 4}, 1: {2, 3, 4}, 2: {3, 4}, 3: {4}},
        {0: {1, 4}, 1: {2}, 2: {3}, 3: {4}, 4: {0}},
        {0: {1, 2, 3, 4}},
        {0: {1, 2, 3, 4}, 1: {2, 4}, 2: {3}, 3: {4}, 4: {1}},
    ]


def _test_network_switch_bridged_backends(core_topologies_dir, image_path, request, runner, scenario_fun):
    """
    0>>>  ifconfig eth0 10.0.0.1 netmask 255.255.0.0 up ; echo -n exit code:$?

    1>>>  ifconfig eth0 10.0.0.2 netmask 255.255.0.0 up ; echo -n exit code:$?
    1>>>  ifconfig eth1 10.1.0.1 netmask 255.255.0.0 up ; echo -n exit code:$?

    2>>>  ifconfig eth0 10.1.0.2 netmask 255.255.0.0 up ; echo -n exit code:$?
    2>>>  ifconfig eth1 10.2.0.1 netmask 255.255.0.0 up ; echo -n exit code:$?

    3>>>  ifconfig eth0 10.2.0.2 netmask 255.255.0.0 up ; echo -n exit code:$?
    3>>>  ifconfig eth1 10.3.0.1 netmask 255.255.0.0 up ; echo -n exit code:$?

    4>>>  ifconfig eth0 10.3.0.2 netmask 255.255.0.0 up ; echo -n exit code:$?
    """
    checks = [
        {
            0: [
                '10.0.0.2'
            ],
            1: [
                '10.1.0.2'
            ],
            2: [
                '10.2.0.2'
            ],
            3: [
                '10.3.0.2'
            ]
        }
    ]

    def check(x: int, ip: str):
        cmd = 'exec -v --node-id {x} "ping -c 1 {ip}"'.format(x=x, ip=ip)
        runner.run_mwcli_command(shlex.split(cmd))

    scenario = scenario_fun(image_path, request, core_topologies_dir)
    connection_mode = scenario['network']['backend']['connection_mode']
    if connection_mode not in runner.connection_modes:
        force_snapshot_boot = False
        runner.connection_modes.add(connection_mode)
    else:
        force_snapshot_boot = True

    brctl_output_before = subprocess.check_call(['brctl', 'show'])
    ebtables_before = subprocess.check_call(['ebtables', '-L'])
    runner.start_scenario(scenario, force_snapshot_boot=force_snapshot_boot)
    for i in range(len(scenario['network']['core']['topologies'])):
        runner.step()
        if i == 0:
            for x, ips in checks[0].items():
                for ip in ips:
                    check(x, ip)
    brctl_output_after = subprocess.check_call(['brctl', 'show'])
    ebtables_after = subprocess.check_call(['ebtables', '-L'])
    # check cleanup done correctly
    assert brctl_output_before == brctl_output_after, 'network backend cleanup not working'
    assert ebtables_before == ebtables_after, 'network backend cleanup not working'
