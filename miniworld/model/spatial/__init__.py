
# TODO: RENAME MODULE!
import logging

from miniworld.log import get_logger
from miniworld.util import PathUtil

_logger = None


# TODO: BETTER WAY THAN LOG FUNCTION?
def logger():
    global _logger
    if _logger is None:
        _logger = get_logger("Spatial Backend")
        _logger.addHandler(logging.FileHandler(PathUtil.get_log_file_path("spatial_backend.txt")))
    return _logger
