import subprocess

import time

from miniworld.service.shell.shell import StreamPortal


class TestStreamPortal:
    def test_log_writer(self):
        log_writer = StreamPortal()
        log_writer.start()
        orig_sel_map = log_writer.selector.get_map()
        p = subprocess.Popen('for i in `seq 1 9`; do echo $i; done', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_writer.register_fh(p.stdout, 'stdout')
        log_writer.register_fh(p.stderr, 'stderr')
        p.wait()
        p2 = subprocess.Popen('echo foo', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_writer.register_fh(p2.stdout, 'stdout')
        log_writer.register_fh(p2.stderr, 'stderr')
        p2.wait()
        time.sleep(1)
        log_writer.stop()
        log_writer.unregister_fh(p.stdout)
        log_writer.unregister_fh(p.stderr)
        log_writer.unregister_fh(p2.stdout)
        log_writer.unregister_fh(p2.stderr)

        # check process logs are captured and multiplexed to file
        with open(log_writer.log_filename) as f:
            assert f.read() == '''stdout: 1
stdout: 2
stdout: 3
stdout: 4
stdout: 5
stdout: 6
stdout: 7
stdout: 8
stdout: 9
stdout: foo
'''

        # check there is no state leftover
        assert log_writer.writer_thread is None
        assert log_writer.prefixes == {}
        assert log_writer.descriptor_buffers == {}
        assert log_writer.selector.get_map() == orig_sel_map
