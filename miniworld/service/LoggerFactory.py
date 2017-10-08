import logging
from threading import Lock
from typing import Tuple

from miniworld import singletons
from miniworld.util.decorators import memoize_pos_args


class LoggerFactory:
    """ Provides logger for services and specific node loggers which
    can be used to differentiate logs from nodes via their id """

    def __init__(self):
        self._loggers = []
        self._lock = Lock()

    @memoize_pos_args
    def get_logger(self, name: Tuple[type, str], formatter=None, handlers=None, log_level=None, **kwargs):
        """
        Get a logger with `name` and the specified `log_level`.
        A formatter from `logging.Formatter` has to be supplied too!
        """

        if log_level is None:
            log_level = singletons.config.get_log_level()

        if formatter is None:
            formatter = self.get_std_formatter()

        if not isinstance(name, str):
            name = '{}.{}'.format(name.__module__, name.__class__.__name__)

        # create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        # configure stream handler
        if handlers is None:
            handler = self.get_stdout_handler(formatter=formatter, log_level=log_level)
            handlers = [handler]

        # if handlers exist, assume handlers are already added
        if not logger.handlers:
            for handler in handlers:
                logger.addHandler(handler)

        self.add_logger(logger)
        return logger

    @memoize_pos_args
    def get_node_logger(self, node_id, log_level=None):
        """ Get a colored logger for a node with id `node_id`.
        A file handler will be created which logs to the standard log directory.
        """

        from colorlog import ColoredFormatter

        if log_level is None:
            log_level = singletons.config.get_log_level()

        formatter_str_time = "%(levelname)s %(name)s %(asctime)s %(module)s: %(message)s"
        format_str = "%(message)s" if not singletons.config.is_debug() else formatter_str_time
        formatter = ColoredFormatter(
            "%(blue)s{}>>>%(reset)s %(log_color)s {fmt_str}".format(node_id, fmt_str=format_str),
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        )

        logger = self.get_logger(str(node_id), formatter, log_level=log_level)

        logger.addHandler(self.get_file_handler("node_%s.txt" % node_id))

        return logger

    def add_logger(self, logger):
        with self._lock:
            self._loggers.append(logger)

    def set_log_level(self, level):
        with self._lock:
            for logger in self._loggers:
                # print("setting log level '%s' for '%s'" % (level, logger.name), file=sys.stderr)
                logger.setLevel(level)

    @staticmethod
    def get_stdout_handler(formatter=None, log_level=None):
        if formatter is None:
            formatter = LoggerFactory.get_std_formatter()
        if log_level is None:
            log_level = singletons.config.get_log_level()

        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        return handler

    @staticmethod
    def get_std_formatter():
        return logging.Formatter("%(levelname)s %(module)s.%(funcName)s: %(message)s")

    @staticmethod
    def get_file_handler(log_file_name):
        from miniworld.util import PathUtil
        return logging.FileHandler(PathUtil.get_log_file_path(log_file_name))
