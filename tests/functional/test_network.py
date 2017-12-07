import os

import pytest

from tests.functional.conftest import create_runner, assert_topologies_equal


@pytest.fixture(scope='module')
def runner(tmpdir_factory, image_path, request, config_path, core_topologies_dir):
    runner = create_runner(tmpdir_factory, request, config_path)

    scenario = {
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
                "connection_mode": "single",
                "execution_mode": {
                    "name": "iproute2",
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

    with runner() as r:
        yield r, scenario


@pytest.fixture
def snapshot_runner(runner):
    runner, scenario = runner
    runner.start_scenario(scenario)
    yield runner
    runner.stop(hard=False)


def test_info_connections(snapshot_runner):
    # mgmt network
    connections = {'1': ['mgmt'],
                   '2': ['mgmt'],
                   '3': ['mgmt'],
                   '4': ['mgmt'],
                   '5': ['mgmt'],
                   }
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)

    # chain
    connections = {'1': ['mgmt', '2'],
                   '2': ['mgmt', '3'],
                   '3': ['mgmt', '4'],
                   '4': ['mgmt', '5'],
                   '5': ['mgmt'],
                   }
    snapshot_runner.step()
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)

    # clique
    connections = {'1': ['mgmt', '2', '3', '4', '5'],
                   '2': ['mgmt', '3', '4', '5'],
                   '3': ['mgmt', '4', '5'],
                   '4': ['mgmt', '5'],
                   '5': ['mgmt'],
                   }
    snapshot_runner.step()
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)

    # cycle
    connections = {'1': ['mgmt', '2', '5'],
                   '2': ['mgmt', '3'],
                   '3': ['mgmt', '4'],
                   '4': ['mgmt', '5'],
                   '5': ['mgmt'],
                   }
    snapshot_runner.step()
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)

    # star
    connections = {'1': ['mgmt', '2', '3', '4', '5'],
                   '2': ['mgmt'],
                   '3': ['mgmt'],
                   '4': ['mgmt'],
                   '5': ['mgmt'],
                   }
    snapshot_runner.step()
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)

    # wheel
    connections = {'1': ['mgmt', '2', '3', '4', '5'],
                   '2': ['mgmt', '3', '5'],
                   '3': ['mgmt', '4'],
                   '4': ['mgmt', '5'],
                   '5': ['mgmt'],
                   }
    snapshot_runner.step()
    res = snapshot_runner.get_connections()
    assert_topologies_equal(res, connections)
