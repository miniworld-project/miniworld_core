import json
import subprocess
from collections import OrderedDict

import pytest
import sys

import time

from tests.acceptance.conftest import create_runner, strip_output


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


@pytest.mark.skip(reason='old test')
def test_ping(snapshot_runner):
    res = snapshot_runner.run_mwcli_command(['ping']).decode()
    assert strip_output(res) == 'pong'


@pytest.mark.skip(reason='old test')
def test_info_scenario(snapshot_runner):
    res = snapshot_runner.run_mwcli_command(['info', 'scenario']).decode()
    with open(snapshot_runner.scenario, 'r') as f:
        assert json.dumps(json.loads(strip_output(res)), sort_keys=True) == json.dumps(json.load(f), sort_keys=True)


@pytest.mark.skip(reason='Stdout not passed from pytest :/ How to fix this?')
def test_shell(snapshot_runner):
    shell = subprocess.Popen(['mwcli', 'shell', '--node-id', '1'], stdin=subprocess.PIPE, stdout=sys.stdout,
                             stderr=sys.stderr)
    time.sleep(5)
    shell.communicate(b'\n')
    shell.communicate(b'ifconfig')
