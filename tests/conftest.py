import gzip
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from copy import deepcopy
from io import BytesIO
from typing import List, Dict

import pytest
import requests

from miniworld.util import JSONConfig

devnull = open(os.devnull, "w")


@pytest.fixture(scope='session')
def config_path(tmpdir_factory):
    return str(tmpdir_factory.mktemp('config').join('config.json'))


def pytest_addoption(parser):
    parser.addoption("--no-server", action="store_true",
                     help="Start the miniworld server from outside")


def strip_output(output):
    return '\n'.join(output.split('\n')[:-1])


@pytest.fixture(scope='session')
def image_path():
    image_url = 'https://downloads.openwrt.org/chaos_calmer/15.05.1/x86/kvm_guest/openwrt-15.05.1-x86-kvm_guest-combined-ext4.img.gz'

    image_name = os.path.basename(image_url)
    # always use the same file path to prevent multiple downloads
    image_path = str(os.path.join(tempfile.gettempdir(), image_name))

    if not os.path.exists(image_path):
        print(('downloading {} to {}'.format(image_url, image_path)))
        response = requests.get(image_url)
        buf = BytesIO(response.content)
        gzip_data = gzip.GzipFile(fileobj=buf)
        with open(image_path, 'wb') as f:
            f.write(gzip_data.read())
    return image_path


def create_runner(tmpdir_factory, request, config_path):
    class Runner(object):
        def __init__(self):
            self.scenario = str(tmpdir_factory.mktemp('scenarios').join('scenario.json'))
            self.config = config_path
            self.server_proc = None
            # self.is_start_server = not request.config.getoption("--no-server")

        def __enter__(self) -> 'Runner':
            self.start()
            return self

        def __exit__(self, type, value, traceback):
            self.stop(hard=True)

        def start(self):
            env = deepcopy(os.environ)
            env.update({'CONFIG': self.config})
            self.connect_to_server()

        @staticmethod
        def run_mwcli_command(custom_args: List[str], *args, **kwargs) -> bytes:
            return subprocess.check_output(['mwcli', '--addr', os.environ.get('MW_SERVER_ADRR', '127.0.0.1')] + custom_args,
                                           *args, **kwargs)
        @staticmethod
        def run_mwcli_command_silently(custom_args: List[str], *args, **kwargs) -> bytes:
            return subprocess.check_call(['mwcli', '--addr', os.environ.get('MW_SERVER_ADRR', '127.0.0.1')] + custom_args,
                                           *args, stdout=devnull, stderr=devnull, **kwargs)
        @staticmethod
        def run_mwcli_command_json_result(custom_args: List[str]) -> Dict:
            return json.loads(strip_output(Runner.run_mwcli_command(custom_args).decode()))

        def stop(self, hard=True):
            # check for rpc errors
            self.check_for_errors()
            # shut down gracefully
            self.run_mwcli_command(['stop'])
            if hard:
                if self.server_proc:
                    self.server_proc.kill()

                    def hard_shutdown(*args, **kwargs):
                        if not self.server_proc.poll() is not None:
                            print('graceful shutdown did not succeed')
                            self.server_proc.send_signal(signal.SIGKILL)
                            signal.alarm(0)

                            assert False

                    signal.signal(signal.SIGALRM, hard_shutdown)
                    signal.alarm(5)
                    self.server_proc.wait()

        def reset(self):
            self.stop(hard=False)
            self.start_scenario(self.scenario)

        def start_scenario(self, scenario, force_snapshot_boot=False):
            '''
            Parameters
            ----------
            scenario: dict
            '''
            with open(self.scenario, 'w') as f:
                scenario_json = json.dumps(scenario, indent=4, sort_keys=True)
                f.write(scenario_json)
                f.flush()
                print(('scenario:\n{}'.format(scenario_json)))
                options = []
                if force_snapshot_boot:
                    options += ['-fs']
                self.run_mwcli_command(['start'] + options + [f.name])

        def check_for_errors(self):
            self.run_mwcli_command(['ping'])

        def step(self):
            self.run_mwcli_command(['step'])

        def get_connections(self):
            '''
            Returns
            -------
            dict
            '''
            return self.run_mwcli_command_json_result(['info', 'connections'])

        def get_links(self):
            '''
            Returns
            -------
            dict
            '''
            return self.run_mwcli_command_json_result(['info', 'links'])

        def get_distances(self):
            '''
            Returns
            -------
            dict
            '''
            return self.run_mwcli_command_json_result(['info', 'distances'])

        def get_addr(self):
            '''
            Returns
            -------
            dict
            '''
            return self.run_mwcli_command_json_result(['info', 'addr'])

        @staticmethod
        def connect_to_server():
            print('connecting to server')
            while 1:
                try:
                    Runner.run_mwcli_command_silently(['ping'])
                    sys.stderr.write('.')
                    return
                except subprocess.CalledProcessError:
                    pass

    return Runner


@pytest.fixture
def runner(tmpdir_factory, config_path, request):
    return create_runner(tmpdir_factory, request, config_path)


@pytest.fixture(scope='session')
def core_topologies_dir():
    return 'tests/core_topologies/'
