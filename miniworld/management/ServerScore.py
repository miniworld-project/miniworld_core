import re

import psutil
from multiprocessing import cpu_count

from miniworld.util import ConcurrencyUtil


def factory():
    return ServerScore

# TODO: add kvm capability


class ServerScore(object):

    SCORE_CPU = "cpu"
    SCORE_FREE_MEM = "free_mem"

    def get_score(self):
        # in MB
        free_mem = psutil.virtual_memory().available / (1024 ** 2)

        # include system load
        total_bogomips = self.get_bogomips() * ConcurrencyUtil.cpu_count()
        # network_speed =
        return \
            {
                self.SCORE_CPU: total_bogomips,
                self.SCORE_FREE_MEM: free_mem
            }

    @staticmethod
    def get_cpu_score(score):
        return score[ServerScore.SCORE_CPU]

    @staticmethod
    def get_free_mem_score(score):
        return score[ServerScore.SCORE_FREE_MEM]

    @staticmethod
    def get_bogomips():
        '''

        Returns
        -------
        float
        '''
        with open("/proc/cpuinfo") as f:
            output = f.read()
            return float(re.search("bogomips\s+:\s+(.*)", output).group(1))
