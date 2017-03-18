import json
import os
import tempfile

import subprocess

import pytest
import sys

devnull = open(os.devnull, "w")


class Runner(object):
    def start_scenario(self, scenario):
        '''

        Parameters
        ----------
        scenario: dict

        Returns
        -------

        '''
        with tempfile.NamedTemporaryFile() as f:
            scenario_json = json.dumps(scenario, indent=4)
            f.write(scenario_json)
            f.flush()
            print('scenario:\n{}'.format(scenario_json))
            subprocess.check_call(['./mw.py', 'start', f.name])

    def check_for_errors(self):
        subprocess.check_call(['./mw.py', 'ping'])


@pytest.fixture
def runner():
    return Runner()


@pytest.fixture
def server(runner):
    os.system('which python')
    subprocess.check_call(['python', '-c', 'import netifaces'])

    server_proc = subprocess.Popen(['./start_server.sh'])
    sys.stderr.write('server started\n')
    connect_to_server()
    yield server_proc

    # check for rpc errors
    runner.check_for_errors()

    server_proc.kill()
    subprocess.Popen(['./cleanup.sh'], stdout=devnull, stderr=devnull)
    sys.stderr.write('server stopped\n')


def connect_to_server():
    print('connection to server')
    while 1:
        try:
            subprocess.check_call(['./mw.py', 'ping'], stdout=devnull, stderr=devnull)
            sys.stderr.write('.')
            return
        except subprocess.CalledProcessError:
            pass
