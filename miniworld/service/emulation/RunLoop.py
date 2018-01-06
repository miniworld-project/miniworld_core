from time import time
from timeit import timeit

from miniworld.singletons import singletons
from miniworld.concurrency.ExceptionStopThread import ExceptionStopThread

__author__ = 'Nils Schmidt'


class RunLoop(ExceptionStopThread):
    """

    Attributes
    ----------
    __last_check : int
    simulation_manager : SimulationManager
    time_step : float
    """

    def __init__(self, simulation_manager):
        self._logger = singletons.logger_factory.get_logger(self)
        super(RunLoop, self).__init__(Exception)
        self.__last_check = 0
        self.simulation_manager = simulation_manager
        self.time_step = singletons.config.get_time_step()

    def _run(self):

        def store_last_check_timestamp():
            # store the last timestamp of this check
            self.__last_check = time()

        store_last_check_timestamp()
        while not self.shall_terminate():

            # measure method execution time
            exec_time = timeit(self.execute_this, number=1)
            if exec_time > self.time_step:
                self._logger.critical("the execution time of the '%s' method is longer than a time step (%s). Took %s",
                                      self._run.__name__, self.time_step, exec_time)

            # wait the remaining time until a time step passed
            wait_time = self.time_step - exec_time
            # but not more than a time step
            wait_time = 0 if wait_time > self.time_step else wait_time
            self._logger.debug("sleeping %f", wait_time)
            self.shall_terminate_event.wait(timeout=wait_time)

            self._logger.info("took: %s", time() - self.__last_check)

            store_last_check_timestamp()

        self._logger.info("terminating run loop ...")

    def execute_this(self):
        self._logger.debug("_run ...")
        self.simulation_manager.step(1)
