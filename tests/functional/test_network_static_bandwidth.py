import os
from copy import deepcopy

import pytest

from tests.conftest import create_runner


@pytest.fixture(scope='module')
def runner(tmpdir_factory, image_path, request, config_path, core_topologies_dir):
    runner = create_runner(tmpdir_factory, request, config_path)

    scenario = {
        "scenario": "",
        "walk_model": {
            "name": "core"
        },
        "cnt_nodes": 3,
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
                    "parallel": False,
                    "batch": False,
                    "one_shell_call": False
                }
            },
            "links": {
                "bandwidth": 55296000
            },
            "core": {
                "topologies": [
                    [0, os.path.join(core_topologies_dir, "chain5.xml")]
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
    runner.start_scenario(scenario, force_snapshot_boot=True)
    yield runner
    runner.stop(hard=False)


def test_info_links(snapshot_runner):
    links_mgmt = {
        # no link impairment for management network
        u"('1', 'mgmt')": None,
        u"('2', 'mgmt')": None,
        u"('3', 'mgmt')": None,
    }
    links_full = deepcopy(links_mgmt)
    # static link impairment here
    links_full.update({
        u"('1', '2')": {u'loss': u'0', u'bandwidth': u'55296000'},
        u"('2', '3')": {u'loss': u'0', u'bandwidth': u'55296000'},
    })

    res = snapshot_runner.get_links()
    assert res == links_mgmt

    snapshot_runner.step()
    res = snapshot_runner.get_links()
    assert res == links_full


def test_info_distances(snapshot_runner):
    distances = {
        "('1', '2')": "1",
        "('1', '3')": "-1",
        "('2', '3')": "1",
    }
    res = snapshot_runner.get_distances()
    assert res == {}

    snapshot_runner.step()
    res = snapshot_runner.get_distances()
    assert res == distances


def test_info_addr(snapshot_runner):
    snapshot_runner.step()
    print(snapshot_runner.get_addr())
