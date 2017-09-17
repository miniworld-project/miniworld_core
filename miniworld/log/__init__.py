import logging
from threading import Lock

from miniworld import Constants
from miniworld.Config import config
from miniworld.decorators import memoize_pos_args
from miniworld.errors import Unsupported

__author__ = 'Nils Schmidt'

# TODO: TICKET #13 (change default log level and make it customizable via the global config)


def get_log_level():
    import logging
    from miniworld.Config import config
    log_level_str = config.get_log_level().upper()
    if hasattr(logging, log_level_str):
        return getattr(logging, log_level_str)

    raise Unsupported("The specified log level '%s' is unknown!" % log_level_str)


loggers = []
lock = Lock()


def add_logger(logger):
    with lock:
        loggers.append(logger)


def set_log_level(level):
    with lock:
        for logger in loggers:
            log.debug("setting log level '%s' for '%s'" % (level, logger.name))
            logger.setLevel(level)


@memoize_pos_args
def get_logger(name, formatter=None, handlers=None, log_level=None, **kwargs):
    """
    Get a logger with `name` and the specified `log_level`.
    A formatter from `logging.Formatter` has to be supplied too!
    """

    if log_level is None:
        log_level = get_log_level()

    if formatter is None:
        formatter = get_std_formatter()

    # prevents bugs
    name = str(name)

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # configure stream handler
    if handlers is None:

        handler = get_stdout_handler(formatter=formatter, log_level=log_level)
        # add handler
        logger.addHandler(handler)
    else:
        for handler in handlers:
            logger.addHandler(handler)

    add_logger(logger)
    return logger


def get_stdout_handler(formatter=None, log_level=None):
    if formatter is None:
        formatter = get_std_formatter()
    if log_level is None:
        log_level = get_log_level()

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    return handler


def get_std_formatter():
    return logging.Formatter("%(levelname)s %(name)s %(funcName)s: %(message)s")


# default logger
formatter_str_time = "%(levelname)s %(name)s %(asctime)s %(module)s: %(message)s"
log = get_logger(Constants.PROJECT_NAME, logging.Formatter(formatter_str_time))
add_logger(log)


@memoize_pos_args
def get_node_logger(node_id, log_level=None):
    """ Get a colored logger for a node with id `node_id`.
    A file handler will be created which logs to the standard log directory.
    """

    from colorlog import ColoredFormatter

    if log_level is None:
        log_level = get_log_level()

    format_str = "%(message)s" if not config.is_debug() else formatter_str_time
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

    logger = get_logger(node_id, formatter, log_level=log_level)

    logger.addHandler(get_file_handler("node_%s.txt" % node_id))

    return logger


def get_file_handler(log_file_name):
    from miniworld.util import PathUtil
    return logging.FileHandler(PathUtil.get_log_file_path(log_file_name))
