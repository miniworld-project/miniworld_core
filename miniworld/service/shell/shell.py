import contextlib
import re
import selectors
import shlex
import subprocess
from collections import defaultdict
from subprocess import CalledProcessError
from threading import Lock

from miniworld.concurrency.ExceptionStopThread import ExceptionStopThread
from miniworld.model.ResetableInterface import ResetableInterface
from miniworld.singletons import singletons
from miniworld.util import PathUtil

SELECT_TIMEOUT = 0.5

__author__ = 'Nils Schmidt'


class ShellHelperError(BaseException):
    pass


class MyCalledProcessError(CalledProcessError):
    def __str__(self):
        return "Command '%s' returned non-zero exit status %d. Stderr: %s" % (self.cmd, self.returncode, self.output)


class BackgroundProcessError(ShellHelperError):
    pass


def run_shell(cmd, *args, **kwargs):
    """

    Parameters
    ----------
    cmd
    args
    kwargs

    Returns
    -------
    str
    """
    bufsize = kwargs.get("buf_size", -1)
    cmd_as_list = shlex.split(cmd)
    # TODO: check if bufsize improves performance
    return subprocess.check_output(cmd_as_list, *args, bufsize=bufsize, **kwargs)

    # TODO: check if commands improves performance in constrast to subprocess
    # exit_code, stdout = commands.getstatusoutput(cmd)
    #
    # if exit_code != 0:
    #     raise ValueError("Command '%s' exited with code: '%s'. Stdout: '%s'" % (cmd, exit_code, stdout))
    # return stdout


# TODO: DOC
def run_shell_get_output(cmd, shell=False):
    """
    Use the system shell for pipes etc!.
    Parameters
    ----------
    cmd

    Returns
    -------
    str
        stdout

    Raises
    ------
    MyCalledProcessError
    """
    p, cmd = run_sub_process_popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    stdout, stderr = p.communicate()
    if p.returncode != 0 and stderr:
        raise MyCalledProcessError(p.returncode, p.args, output=stderr)
    return stdout


def run_sub_process_popen(cmd, stdout=None, stderr=None, stdin=None, **kwargs):
    cmd = fmt_cmd_template(cmd)

    cmd_as_list = shlex.split(cmd)
    # note: do not use subprocess.PIPE! May cause deadlock!
    # see: http://thraxil.org/users/anders/posts/2008/03/13/Subprocess-Hanging-PIPE-is-your-enemy/
    p = subprocess.Popen(cmd_as_list, close_fds=True, stdout=stdout, stderr=stderr, stdin=stdin, **kwargs)
    singletons.log.debug("started %s", ' '.join(p.args) + (" (PID = %s)" % p.pid))
    return p, cmd


def fmt_shell_cmd_log_file_prologue(cmd):
    """ Create the prologue for a log file which holds the result of the execution of `cmd` """
    return """$ %s
%s
""" % (cmd, "-" * 50)


def fmt_cmd_template(cmd):
    """ Format the cmd template `cmd` so that in can be used e.g. for a os.system call """
    return re.sub("\s+", " ", cmd)


class StreamPortal:
    """
    Read from all file streams and multiplex the streams line-buffered into a log file.

    Attributes
    ----------
    descriptor_buffers : dict<file, str>
        For each descriptor a buffer.
    prefixes : dict<file, str>
        For each descriptor a prefix for logging.
    fh_logfile : file

    writer_thread : ExceptionStopThread
    """

    def __init__(self, log_filename=None):
        """

        Parameters
        ----------
        log_filename : str, optional (default is "background_shell_processes")

        Returns
        -------
        """

        self._logger = singletons.logger_factory.get_logger(self)

        if log_filename is None:
            log_filename = "background_shell_processes.txt"
        self.log_filename = PathUtil.get_log_file_path(log_filename)

        self.fh_logfile = None
        self.descriptor_buffers = defaultdict(str)
        self.selector = selectors.DefaultSelector()
        self.prefixes = {}

        self.writer_thread = None  # type: ExceptionStopThread

    def reset_fd_state(self):
        for selector_key in self.selector.get_map().values():
            _file = selector_key.fileobj
            if _file.closed:
                self._logger.debug("removing closed file '%s' from '%s'", _file, self.__class__.__name__)
                self.unregister_fh(_file)

    def stop(self):
        self.writer_thread.terminate()
        self.writer_thread.join()
        self.flush()
        self.writer_thread = None

    def start(self):
        self._logger.info("starting log writer (file: '%s')", self.log_filename)
        if self.fh_logfile is None:
            self.fh_logfile = open(self.log_filename, "w")
        self.writer_thread = ExceptionStopThread.run_fun_threaded_n_log_exception(target=self.check,
                                                                                  tkwargs=dict(name="LogWriter"))
        self.writer_thread.daemon = True
        self.writer_thread.start()

    def register_fh(self, sock, prefix):
        self.selector.register(sock, selectors.EVENT_READ)
        self.prefixes[sock] = prefix

    def unregister_fh(self, fh):
        with contextlib.suppress(KeyError):
            # may be empty
            del self.descriptor_buffers[fh]
        del self.prefixes[fh]
        self.selector.unregister(fh)

    def check(self):
        while True:

            if self.writer_thread.shall_terminate():
                self._logger.debug("stopping '%s'", self.__class__.__name__)
                return

            events = self.selector.select(timeout=SELECT_TIMEOUT)
            # SelectorKey, int
            for key, mask in events:

                fd = key.fileobj

                prefix = self.prefixes.get(fd, "N/A")
                data = fd.read(1)

                if data:
                    self.descriptor_buffers[fd] += data.decode('utf-8')

                    # line-buffered
                    try:
                        newline_idx = self.descriptor_buffers[fd].index("\n")
                    # ValueError: substring not found
                    # for "\n"
                    except ValueError:
                        continue

                    data = self.descriptor_buffers[fd][:newline_idx + 1]

                    self.fh_logfile.write('%s: %s' % (prefix, data))
                    self.fh_logfile.flush()

                    # remove written byttes from string buffer
                    self.descriptor_buffers[fd] = self.descriptor_buffers[fd][newline_idx + 1:]

    def flush(self):
        for fd, data in self.descriptor_buffers.items():
            if data:
                prefix = self.prefixes.get(fd, "N/A")
                self.fh_logfile.write('%s: %s' % (prefix, data))
                self.fh_logfile.flush()

        keys = list(self.descriptor_buffers.keys())
        for key in keys:
            del self.descriptor_buffers[key]


FOREGROUND_SHELL_LOG_PATH = PathUtil.get_log_file_path("foreground_shell_commands.txt")


class ShellHelper(ResetableInterface):
    """
    Provides help for starting shell process in fore- and background.
     For the background threads, the stdout/stderr file descriptors are read
     and further process by the :py:class:`.LogWriter` thread.

     All started background processes are stored in :py:attr:`subprocesses`.
     Furthermore all bg processes are monitored for their return codes.

    Note that creating an instance of this class creates two threads: py:class:`.LogWriter` and the bg process checker.
    Therefore, one should use the singleton object!

    Attributes
    ----------
    log_writer
    lock
    subprocess : list<subprocess.Popen>
    bg_checker_thread : ExceptionStopThread
    """

    lock = Lock()
    subprocesses = []
    log_writer = None

    def __init__(self, garbage_collect=True):
        """

        Parameters
        ----------
        garbage_collect : bool, optional (default is False)
            Reset all started background subprocesses with the `reset` method.
            NOTE: the `reset` method is not called from inside this class!

        Returns
        -------
        str
            Output of the shell command
        """
        self.garbage_collect = garbage_collect
        self.bg_checker_thread = None
        self.start_bg_checker_thread()
        self._logger = True

    ###############################################################
    # Background Error Checking
    ###############################################################

    def check_error_codes(self):
        # check processes every x seconds for return codes
        while True:
            if self.bg_checker_thread.shall_terminate():
                return
            self.bg_checker_thread.shall_terminate_event.wait(5.0)

            with self.lock:

                self._logger.debug("checking bg processes return codes ...")
                subprocesses_to_delete = []
                for subproc in self.subprocesses:
                    singletons.log.debug("%s => %s", subproc, subproc.returncode)
                    if subproc.returncode > 0:
                        exception = BackgroundProcessError(
                            "The subprocess '%s' exited with error code '%s'. See the log file for the output!" % (
                                subproc, subproc.returncode))
                        self.bg_checker_thread.exception_handler(exception)
                        subprocesses_to_delete.append(subproc)
                for subproc in subprocesses_to_delete:
                    del self.subprocesses[subproc]

    # TODO: REMOVE?
    def start_bg_checker_thread(self):
        return
        self.bg_checker_thread = ExceptionStopThread.run_fun_threaded_n_log_exception(target=self.check_error_codes,
                                                                                      tkwargs=dict(
                                                                                          name="BG Process Checker"))
        self.bg_checker_thread.start()
        self._logger.info("starting bg process checker thread ...")

    # TODO: REMOVE?
    def stop_bg_checker_thread(self):
        return
        self.bg_checker_thread.terminate()
        self._logger.info("stopping bg process checker thread ...")
        self.bg_checker_thread.join()
        self._logger.info("stopping bg process checker thread [done]")

    ###############################################################
    ###
    ###############################################################

    @staticmethod
    def run_shell_with_input(cmd, _input):
        """
        Run the shell command `cmd` and supply `_input` as stdin.

        Parameters
        ----------
        cmd : str
        _input : str

        Returns
        -------
        str

        Raises
        ------
        MyCalledProcessError
        """
        # magic '\n' seems to be required for iproute2
        _input += '\n'
        singletons.log.info("'%s <<<\"%s\"'", cmd, _input)

        cmd = shlex.split(cmd)
        p = subprocess.Popen(cmd, close_fds=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        stdout, stderr = p.communicate(_input.encode())
        if p.returncode == 0:
            return stdout
        else:
            raise MyCalledProcessError(p.returncode, p.args, output=stderr)

    # TODO: DOC
    def run_shell(self, node_id, cmd, prefixes=None):
        if prefixes is None:
            prefixes = ["N/A"]

        # if prefixes are supplied as tuple
        prefixes = list(prefixes)

        prefix_str = '>>> '.join(map(str, [node_id] + prefixes))
        nlog = singletons.logger_factory.get_node_logger(node_id)
        cmd = fmt_cmd_template(cmd)

        # TODO: #2: ABSTRACTION!
        nlog.info('%s: %s', '>>> '.join(prefixes), cmd)

        try:
            output = run_shell(cmd)
            with open(FOREGROUND_SHELL_LOG_PATH, "a") as f:
                f.write("%s '%s'\n:%s\n" % (prefix_str, cmd, output))

            return output
        # TODO:
        except subprocess.CalledProcessError as e:
            self._logger.exception(e)
            raise

    # TODO: Ticket #2
    def run_shell_async(self, node_name, cmd, prefixes=None, take_process_ownership=True, supervise_process=True):
        """

        Parameters
        ----------
        node_name
        cmd
        prefixes
        take_process_ownership : bool, optional (default is True)
            Take care of stopping the process for the simulation reset.

        Returns
        -------

        """

        with self.lock:
            if not self.log_writer:
                self.log_writer = StreamPortal()
                self.log_writer.start()

        if prefixes is None:
            prefixes = ["N/A"]

        prefix_str = '>>> '.join(map(str, [node_name] + prefixes))
        nlog = singletons.logger_factory.get_node_logger(node_name)
        # TODO: #2 : catch/reraise exception if command malformed!
        stdout = None
        stderr = None
        if supervise_process:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        p, cmd = run_sub_process_popen(cmd, stdout=stdout, stderr=stderr)
        nlog.info('%s: %s', '>>> '.join(prefixes), cmd)

        if supervise_process:
            # important: otherwise subprocess blocks!
            self.log_writer.register_fh(p.stdout, prefix_str)
            self.log_writer.register_fh(p.stderr, prefix_str)

        if take_process_ownership and self.garbage_collect:
            with self.lock:
                self.subprocesses.append(p)

        return p

    #########################################
    # Resettable Interface
    #########################################

    def reset(self):
        # TODO: #2 : DOC

        # first stop checking bg processes for return codes
        # then SIGTERM, then SIGKILL

        self._logger.debug("'%s' reset ...", self.__class__.__name__)
        self.stop_bg_checker_thread()
        with self.lock:
            # stop LogWriter first
            if self.log_writer:
                self.log_writer.stop()

            self._logger.warn("sending SIGTERM to all processes ...")
            # TODO: Ticket #2
            self._logger.info("terminating %s subproccesses" % len(self.subprocesses))
            for subproc in self.subprocesses:
                subproc_info = ' '.join(subproc.args) + (" (PID = %s)" % subproc.pid)
                self._logger.debug("terminating '%s'" % subproc_info)
                try:
                    subproc.terminate()
                    TIMEOUT = 5
                    self._logger.debug("waiting for %s to terminate (%s)", subproc_info, TIMEOUT)
                    subproc.wait(timeout=TIMEOUT)
                    self._logger.debug("terminated %s", subproc_info)

                except subprocess.TimeoutExpired as e:
                    self._logger.warn(
                        "Subprocess: '%s' did not shutdown in time (%s). Killing ..." % (subproc_info, TIMEOUT))
                    subproc.kill()
                    subproc.wait()

                if self.log_writer:
                    self.log_writer.unregister_fh(subproc.stdout)
                    self.log_writer.unregister_fh(subproc.stderr)

            # clear subprocesses
            self._logger.debug("cleared subprocesses index ...")
            self.subprocesses = []

            if self.log_writer:
                self.log_writer.reset_fd_state()
                self.log_writer.start()
