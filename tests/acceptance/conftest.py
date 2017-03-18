import gzip
import json
import subprocess
import sys
import tempfile
import urllib2
from StringIO import StringIO

import os
import pytest

devnull = open(os.devnull, "w")
image_path = None


def get_openwrt_image():
    image_url = 'https://downloads.openwrt.org/chaos_calmer/15.05.1/x86/kvm_guest/openwrt-15.05.1-x86-kvm_guest-combined-ext4.img.gz'
    image_name = os.path.basename(image_url)
    global image_path
    image_path = os.path.join(tempfile.gettempdir(), image_name)
    if not os.path.exists(image_path):
        print('downloading {} to {}'.format(image_url, image_path))
        data = StringIO(urllib2.urlopen(image_url).read())
        gzip_data = gzip.GzipFile(fileobj=data)
        with open(image_path, 'w') as f:
            f.write(gzip_data.read())


class Runner(object):
    def __init__(self):
        get_openwrt_image()

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

    @property
    def image_path(self):
        return image_path


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
    # shut down gracefully
    server_proc.kill()

    # def hard_shutdown():
    #     if not server_proc.poll() is not None:
    #         print('graceful shutdown did not succeed')
    #         server_proc.send_signal(signal.SIGKILL)
    #         signal.alarm(0)
    #
    #         assert False
    #
    # signal.signal(signal.SIGALRM, hard_shutdown)
    # signal.alarm(5)
    # server_proc.wait()

    try:
        subprocess.Popen(['./cleanup.sh'], stdout=devnull, stderr=devnull)
    except Exception:
        pass
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
