import contextlib
from time import sleep

import multiprocessing
from concurrent import futures

from miniworld import config

__author__ = 'Nils Schmidt'


def wait_until_fun_returns_true(check_fun, fun, *args, **kwargs):
    """
    Wait until fun(*args, **kwargs) returns something True.

    Parameters
    ----------
    sleep_time int, optional (default is 0.1)

    Returns
    -------
    object
        The value of the function
    """
    sleep_time = kwargs.get("sleep_time", 0.1)
    if "sleep_time" in kwargs:
        del kwargs["sleep_time"]

    while True:
        res = fun(*args, **kwargs)
        if check_fun(res):
            return res
        sleep(sleep_time)

# TODO: DOC
# TODO: introduce more context managers!


@contextlib.contextmanager
def network_provision_parallel():
    from miniworld.Scenario import scenario_config
    cnt_minions = scenario_config.get_network_backend_cnt_minions()
    with tpe(cnt_minions) as executor:
        yield executor


@contextlib.contextmanager
def node_start_parallel():
    from miniworld.Scenario import scenario_config
    parallel = scenario_config.is_parallel_node_starting()
    cnt_minions = cpu_count() if parallel else 1
    with tpe(cnt_minions) as executor:
        yield executor

# @contextlib.contextmanager
# def network_backend_parallel():
#     from miniworld.Scenario import scenario_config
#     cnt_minions = scenario_config.get_network_backend_cnt_minions()
#     with tpe(cnt_minions) as executor:
#         yield executor


@contextlib.contextmanager
def tpe(cnt_minions):
    with futures.ThreadPoolExecutor(max_workers=cnt_minions) as executor:
        yield executor


def cpu_count():
    cnt_minions = multiprocessing.cpu_count()
    return int(round(cnt_minions))
