import os
import subprocess

import pytest
from typing import Dict

from miniworld.util import JSONConfig


@pytest.fixture(scope='session')
def download_examples():
    if not os.path.isdir('examples/'):
        pytest.skip('examples not mounted')

    subprocess.check_call(['./get_images.sh'], cwd='examples/')
    os.system('ls -l examples/')


@pytest.mark.usefixtures('download_examples')
class TestExamples:
    # TODO: examples/batman_adv.json, problem is configurator

    def test_snapshot_boot_single_scenario(self, runner):
        with runner() as r:
            for _ in range(5):
                scenario = JSONConfig.read_json_config('examples/nb_bridged_lan.json')  # type: Dict
                r.start_scenario(scenario)
                r.step()
                r.step()
                r.stop(hard=False)

    # TODO: test stop/step
    @pytest.mark.usefixtures('download_examples')
    def test_snapshot_boot_multiple_scenarios(self, runner):
        with runner() as r:
            scenario = JSONConfig.read_json_config('examples/batman_adv.json')  # type: Dict
            r.start_scenario(scenario)
            for _ in range(5):
                r.step()
            r.stop(hard=False)

            scenario = JSONConfig.read_json_config('examples/nb_bridged_lan.json')  # type: Dict
            r.start_scenario(scenario)
            for _ in range(5):
                r.step()
            r.stop(hard=False)

            scenario = JSONConfig.read_json_config('examples/nb_bridged_wifi.json')  # type: Dict
            r.start_scenario(scenario)
            for _ in range(5):
                r.step()
            r.stop(hard=False)
