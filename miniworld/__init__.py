import atexit
import logging
import os
import shutil
import signal
import sys

from miniworld.Constants import PATH_TMP, PATH_LOGS, PROJECT_NAME, PATH_CLEANUP_SCRIPT
from miniworld.config import Config
from miniworld.errors import AlreadyRunning
from miniworld.service.shell.shell import run_shell
from miniworld.singletons.Singletons import singletons
from miniworld.util import PathUtil

__author__ = 'Nils Schmidt'

"""
Module structure:
    Interchangeable components are located at the following places and are not placed at service/models:
    - network
    - mobility
    - nodes
    - impairment
"""


def init(config_path: str = None, do_init_singletons=True, do_init_db=True):
    """ Init the module by installing signal handlers and creating the temp files """

    Config.set_global_config(config_path or Config.PATH_GLOBAL_CONFIG)
    if do_init_singletons:
        init_singletons()

    if not os.path.exists(Config.PATH_GLOBAL_CONFIG):
        # TODO: render config.json from config sleeve
        singletons.log.info('creating config ...')
        shutil.copy2('sample_configs/config.json', '.')

    # TODO: Ticket #2
    install_signal_handlers()
    singletons.logger_factory.set_log_level(singletons.config.get_log_level())

    clean_miniworld_dir()
    singletons.log.addHandler(logging.FileHandler(PathUtil.get_log_file_path("stdout.txt")))

    if do_init_db:
        init_db()


def init_singletons():
    from miniworld.singletons import SingletonInit
    SingletonInit.init_singletons()


def init_db():
    from miniworld.singletons import singletons
    singletons.db_session.create_session()
    singletons.db_session.clear_state()


def clean_miniworld_dir():
    create_n_check_tmp_files(delete_first=True, create_ramdisk=singletons.config.is_ramdisk_enabled())
    create_log_files_dir()


def umount_ramdisk():
    run_shell("init", "umount {}".format(PATH_TMP))


def try_umount_ramdisk():
    # umount ramdisk
    try:
        singletons.log.info("unmounting ramdisk (if one is mounted)")
        umount_ramdisk()
    except BaseException:
        pass


def create_n_check_tmp_files(delete_first=False, create_ramdisk=False):
    """ Create tmp dirs if not existing yet.

    Raises
    ------
    AlreadyRunning
    """
    if os.path.exists(PATH_TMP):
        if delete_first:
            try:
                shutil.rmtree(PATH_LOGS)
            except BaseException:
                pass

            # umount ramdisk
            try_umount_ramdisk()
        else:
            # Ticket #12
            raise AlreadyRunning("Another instance of %s might be running! Did you invoke the cleanup script '%s'?" % (
                PROJECT_NAME, PATH_CLEANUP_SCRIPT))

    if not os.path.exists(PATH_TMP):
        singletons.log.debug("Creating directory '%s'!", PATH_TMP)
        os.makedirs(PATH_TMP)

    if create_ramdisk:
        if not os.path.ismount(PATH_TMP):

            singletons.log.info("creating ramdisk at '%s'", PATH_TMP)
            # TODO: better way for ramdisk creation?
            run_shell("sudo mount -t ramfs ramfs {}".format(PATH_TMP))
        else:
            singletons.log.info("ramdisk still exists at '%s' ... ", PATH_TMP)


def create_log_files_dir():
    """ Create log dirs if not existing yet """
    singletons.log.warn("(re)creating log directory: '%s' !", PATH_LOGS)
    os.makedirs(PATH_LOGS)


def install_signal_handlers():
    """ Install the signal handlers """

    atexit.register(error_handler, "exit")
    signal.signal(signal.SIGINT, error_handler_sys_exit)
    signal.signal(signal.SIGTERM, error_handler_sys_exit)
    signal.signal(signal.SIGHUP, error_handler_sys_exit)
    signal.signal(signal.SIGUSR1, error_handler)


def uninstall_signal_handlers():
    """ Uninstall the signal handlers """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def error_handler_sys_exit(signum, *args, **kwargs):
    error_handler(signum)
    sys.exit(1)


def error_handler(signum, *args, **kwargs):
    singletons.log.critical("received signal: %s", signum)
    # may not be created yet
    if singletons.simulation_manager:
        singletons.simulation_manager.abort()

    try_umount_ramdisk()
