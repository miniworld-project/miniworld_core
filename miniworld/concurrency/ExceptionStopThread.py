

# encoding: utf-8
import sys

from miniworld.concurrency import StopThread
from miniworld.log import log
from miniworld.model.singletons.Singletons import singletons

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"


class ExceptionStopThread(StopThread.StopThread):
    ''' Adds a wrapper around the run() method and catches the supplied exceptions.
    If an exception occurrs, the thread is stopped and the exception is stored in a local variable
    together with its traceback.

    Functions
    ---------
    exception_handler : Exception -> void

    Examples
    --------
    >>> class Foo(ExceptionStopThread):
    >>> def __init__(self):
    >>>     super(Foo, self).__init__(Exception)
    >>> def _run(self):
    >>>     raise ValueError("")
    >>> t = Foo()
    >>> t.start()
    >>> t.join()
    >>> raise t.raise_objects[0], t.raise_objects[1], t.raise_objects[2]
    '''
    
    def __init__(self, exception_type, *args, **kwargs):
        '''
        Parameters
        ----------
        exception_type : type
            The exception to catch.
        raise_objects : BaseException, None, traceback
            Objects to be passed to raise(...)

        '''
        super(ExceptionStopThread, self).__init__(*args, **kwargs)
        self.raise_objects = None

        self.exception_type = exception_type

    def _run(self):
        ''' Implement in subclass '''
        raise NotImplementedError

    def exception_handler(self, exception):
        '''
        Called if a unhandled exception occurs.

        Parameters
        ----------
        exception
        '''
        pass

    def run(self):
        try:
            self._run()
        except self.exception_type as e:
            log.exception(e)
            self.raise_objects = e, None, sys.exc_info()[2]
            self.exception_handler(e)
            self.terminate()

    # TODO: DOC
    @staticmethod
    def run_fun_threaded_n_log_exception(*args, **kwargs):
        '''

        Parameters
        ----------
        target
        targs
        tkwargs

        Returns
        -------
        Thread
        '''

        target = kwargs.get("target")
        targs = kwargs.get("targs")
        tkwargs = kwargs.get("tkwargs")

        if target:
            del kwargs["target"]
        if targs:
            del kwargs["targs"]
        if tkwargs:
            del kwargs["tkwargs"]

        if targs is None:
            targs = []
        if tkwargs is None:
            tkwargs = {}

        t = ExceptionStopThread(Exception)
        t.daemon = True
        t._run = lambda: target(*args, **kwargs)

        def exception_handler(exception):
            singletons.simulation_errors.append((exception, None, sys.exc_info()[2]))
        t.exception_handler = exception_handler

        return t

    # TODO: DOC
    def run_decorator_threaded_n_log_exception(fun):
        def wrap(*args, **kwargs):
            res = ExceptionStopThread.run_fun_threaded_n_log_exception(fun, targs=args, tkwargs=kwargs)
            return res

        return wrap


if __name__ == '__main__':
    def fail():
        raise Exception("foo")

    ExceptionStopThread.run_fun_threaded_n_log_exception(fail)

    #time.sleep(100)

