import json
from collections import OrderedDict

import pytest

from tests.conftest import create_runner, strip_output


@pytest.fixture(scope='session')
def runner(tmpdir_factory, image_path, request, config_path):
    runner = create_runner(tmpdir_factory, request, config_path)

    scenario = OrderedDict([
        ("scenario", "acceptance_boot"),
        ("cnt_nodes", 1),
        ("provisioning", OrderedDict([
            ("image", image_path),
            ("regex_shell_prompt", "root@OpenWrt:/#")
        ]))
    ])

    with runner() as r:
        yield r, scenario


@pytest.fixture
def snapshot_runner(runner):
    runner, scenario = runner
    runner.start_scenario(scenario, force_snapshot_boot=True)
    yield runner
    runner.stop(hard=False)


def test_info_scenario(snapshot_runner):
    res = snapshot_runner.run_mwcli_command(['info', 'scenario']).decode()
    with open(snapshot_runner.scenario, 'r') as f:
        assert json.loads(strip_output(res), object_pairs_hook=OrderedDict) == json.load(f,
                                                                                         object_pairs_hook=OrderedDict)


def test_ping(snapshot_runner):
    res = snapshot_runner.run_mwcli_command(['ping']).decode()
    assert strip_output(res) == 'pong'
