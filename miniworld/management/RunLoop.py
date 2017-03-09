from time import time
from timeit import timeit

from miniworld import log
from miniworld.concurrency.ExceptionStopThread import ExceptionStopThread

from miniworld.Config import config

__author__ = 'Nils Schmidt'

class RunLoop(ExceptionStopThread):
    '''

    Attributes
    ----------
    __last_check : int
    simulation_manager : SimulationManager
    time_step : float
    '''
    def __init__(self, simulation_manager):
        super(RunLoop, self).__init__(Exception)
        self.__last_check = 0
        self.simulation_manager = simulation_manager
        self.logger = self.simulation_manager.logger
        self.time_step = config.get_time_step()

    def _run(self):

        def store_last_check_timestamp():
            # store the last timestamp of this check
            self.__last_check = time()

        store_last_check_timestamp()
        while not self.shall_terminate():

            # measure method execution time
            exec_time = timeit(self.execute_this, number = 1)
            if exec_time > self.time_step:
                self.logger.critical("the execution time of the '%s' method is longer than a time step (%s). Took %s", self._run.func_name, self.time_step, exec_time)

            # wait the remaining time until a time step passed
            wait_time = self.time_step - exec_time
            # but not more than a time step
            wait_time = 0 if wait_time > self.time_step else wait_time
            self.logger.debug("sleeping %f", wait_time)
            self.shall_terminate_event.wait(timeout = wait_time)

            self.logger.info("took: %s",  time() -  self.__last_check)

            store_last_check_timestamp()

        log.info("terminating run loop ...")

    def execute_this(self):
        self.logger.debug("_run ...")
        self.simulation_manager.step(1)
