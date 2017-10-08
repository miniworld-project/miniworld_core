import re
import socket

from miniworld.errors import Base
from miniworld.service.provisioning.SocketExpect import SocketExpect
from miniworld.singletons import singletons
from miniworld.util import NetUtil
from miniworld.util.NetUtil import read_remaining_data, Timeout

# buffer size for for non-bytewise operations
SOCKET_READ_BUF_SIZE = 65536


class CommandRunner:
    """
    This class is responsible for the command execution of the :py:class:`.REPL`.

    Attributes
    ----------
    sock
    re_shell_prompt
    """

    def __init__(self,
                 replable,
                 timeout,
                 flo,
                 brief_logger=None,
                 interactive_result_stdout_writing=True,
                 verbose_logger=None,
                 shell_prompt=None,
                 logger_echo_commands=False,
                 template_engine_kwargs=None,
                 return_value_checker=None,
                 enter_shell_send_newline=True,
                 ):
        """
        Parameters
        ----------
        replable : REPLable
            The repl reference.
        timeout : float
            Timeout
        flo: file-like-object
            Read the string contents from `flo`.
        brief_logger : logigng.logger
            Logs briefly all commands (log level: info).
            Also used for exception and error logging!
        interactive_result_stdout_writing: bool, optional (default is False)
            Redirect command stdout/stderr to local stdout.
        verbose_logger : logging.Logger, optional (default is None)
            Log complete output! Very verbose.
            Log output if logger given.
            Only if debug mode is on!
            Note: exceptions are only logged with a Logger!
        shell_prompt : str, optional (default is the value from the current scenario config)
            The shell prompt to expect (regular expression, needed to wait for the completion of a command).
            The re engine uses the flags: re.DOTALL | re.MULTILINE.
        logger_echo_commands : bool, optional (default is False)
            If enabled, all executed commands are written to the log file too.
            The shell e.g. echos automatically back, so it is not needed.
        template_engine_kwargs : dict, optional (default is {})
            Use to pass through keyword arguments to the template engine.
        return_value_checker : fun: str -> str -> object, optional, (default is None)
            If supplied, apply the function on output of the REPL after the REPL returned.
            First argument is the command which gets executed, second the result of the execution.
            Raises :py:class:`.REPLUnexpectedResult` if this method raises an exception.
        # TODO: DOC
        enter_shell_send_newline
        """

        if template_engine_kwargs is None:
            template_engine_kwargs = {}
        if shell_prompt is None:
            shell_prompt = singletons.senario_config.get_shell_prompt()

        self._logger = singletons.logger_factory.get_logger(self)
        self.replable = replable
        self.flo = flo
        self.interactive_result_stdout_writing = interactive_result_stdout_writing
        self.brief_logger = brief_logger
        self.verbose_logger = verbose_logger if singletons.config.is_debug() else None
        self.shell_prompt = shell_prompt
        self.log_file_echo_command = logger_echo_commands
        self.template_engine_kwargs = template_engine_kwargs
        self.return_value_checker = return_value_checker
        self.timeout = timeout
        self.enter_shell_send_newline = enter_shell_send_newline

        if self.brief_logger is None:
            raise ValueError("A valid logger must be given!")

        self.sock = None
        self.re_shell_prompt = re.compile(shell_prompt, flags=re.DOTALL | re.MULTILINE)

    def is_reuse_socket(self):
        return hasattr(self.replable, 'uds_socket')

    def __call__(self, *args, **kwargs):
        """
        Execute the code lazily in the REPL.

        1. Wait until the REPL is reachable
        2. Connect
        3. Execute the code line for line and wait for the shell prompt

        Returns
        -------
        generator<socket, str, str, ...>

        Raises
        ------
        REPLUnexpectedResult
            If the `return_value_checker` raised an Exception.
        REPLTimeout
            If the `timeout` occurred while waiting for results from the REPL socket.
        """

        try:
            self.sock = None
            # wait until uds is reachable
            if self.is_reuse_socket():
                if self.replable.uds_socket is None:
                    self.replable.uds_socket = self.replable.wait_until_uds_reachable(return_sock=True)
                self.sock = self.replable.uds_socket
            else:
                self.sock = self.replable.wait_until_uds_reachable(return_sock=True)

            # TODO: old stuff
            # return socket object first
            yield self.sock

            # we may need to press enter first to activate the console/management socket
            self.enter_shell()

            # execute script on socket
            # NOTE: needed to let the generator finish the method execution
            for x in self.execute_script():
                yield x

        except socket.error as e:
            self.brief_logger.exception(e)
        except Timeout as e:
            self.brief_logger.info('sending CTRL-C to shell ...')
            try:
                self.sock.send(b'\x03')
            except socket.error:
                pass
            raise REPLTimeout("The REPL '%s' encountered a timeout (%s) while looking for shell prompt (%s)" % (
                self.replable, self.timeout, self.shell_prompt))

        # finally close socket
        finally:

            try:
                self.close_sockets()

            except AttributeError as e:
                self._logger.exception(e)
                raise ValueError(
                    "The REPLable subclass '%s' did not return a valid socket!" % self.replable.__class__.__name__)

    def close_sockets(self):

        if not self.is_reuse_socket():
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                self._logger.exception(e)

            try:
                self.sock.close()
            except socket.error as e:
                self._logger.exception(e)

    def enter_shell(self):
        """
        Enter the shell before any commands are executed on the socket.
        This is needed to ensure the first output of the socket is the one that corresponds
        to the executed command.

        Raises
        ------
        REPLTimeout
        """
        ENTER_SHELL_CMD = '\n'

        while True:
            if self.verbose_logger:
                self.verbose_logger.debug("sending '%s', timeout: %s", ENTER_SHELL_CMD, self.timeout)
            if self.verbose_logger:
                self.verbose_logger.debug("sending '%s', timeout: %s [done]", ENTER_SHELL_CMD, self.timeout)

            if self.enter_shell_send_newline:
                self.sock.send(b"\n")
            if self.wait_for_command_execution(timeout=self.timeout):
                break
        if self.verbose_logger:
            self.verbose_logger.debug("entered shell ...")

    # TODO: DOC return_value_checker
    def execute_script(self):
        """
        Run the code. Therefore split the string at each newline and send it to the socket.
        Wait for each command until we see the shell prompt.

        Yields
        ------
        str
            The output from the commands.

        Raises
        ------
        REPLUnexpectedResult
            If return_value_checker
        """

        # render script variables
        script = self.replable.render_script_from_flo(self.flo, **self.template_engine_kwargs)

        # run over script lines
        for cmd in script.split("\n"):

            # no empty lines
            if cmd:

                self.brief_logger.info(cmd)
                if self.verbose_logger and self.log_file_echo_command:
                    self.verbose_logger.info("$> '%s'", cmd)

                # execute command
                cmd = cmd + "\n"
                self.sock.send(cmd.encode())

                res = self.wait_for_command_execution(timeout=self.timeout)
                # read all data which is not covered by the regex used for stream searching
                # TODO: use loop here?!
                res += read_remaining_data(self.sock, SOCKET_READ_BUF_SIZE)

                # apply the custom check function
                if self.return_value_checker is not None:
                    try:
                        self.return_value_checker(cmd, res)
                    except Exception as e:
                        raise REPLUnexpectedResult(
                            "The following output is unexpected to the method `return_value_checker`:\n%s" % res) from e

                yield res

    def process_output(self, data):
        """ Write the `data` to the log file as well as to the logger """

        if self.interactive_result_stdout_writing:
            self.brief_logger.debug(data)
            if self.verbose_logger:
                self.verbose_logger.info(data)

        # f.write(data)
        # show results instantly in log file
        # f.flush()

        return data

        # TODO: #68: compile re for better performance
        # TODO: RENAME

    def wait_for_command_execution(self, timeout=None, check_fun=None):
        """ Wait until the command has been seen on the REPL and the shell prompt is visible.

        Parameters
        ----------
        command : str, optional (default is '')
            Check that the command is read from the REPL output,
            therefore it has been send to the REPL.
            Get's escaped, so no conflicts with re special keys can occur.

        Returns
        -------
        str
            The result of executing the command.

        Raises
        ------
        REPLTimeout
            In case of a timeout.
        """
        if check_fun is None:
            def check_fun2(buf, whole_data):
                # TODO: expose via logging config entry
                if self.verbose_logger is not None:
                    self.verbose_logger.debug("expecting '%s', got: '%s'", self.shell_prompt, buf)

                return self.re_shell_prompt.search(whole_data)

            check_fun = check_fun2
        try:
            res = self.process_output(
                SocketExpect(self.sock,
                             check_fun,
                             read_buf_size=SOCKET_READ_BUF_SIZE,
                             timeout=timeout
                             ).read()
            )
        except NetUtil.Timeout as e:
            # netstat_uds = run_shell("netstat -ape -A unix")
            # open_fds = run_shell('ls -l /proc/%s/fd/' % os.getpid())
            # lsof = run_shell('lsof -U')
            # debug:

            # Active Unix Domain Sockets:
            # %s.
            # Open file handles (Unix):
            # %s
            # lsof:
            # %s
            # % (netstat_uds, open_fds, lsof))
            # log exception to node log
            if self.brief_logger:
                self.brief_logger.exception(e)

            raise
        return res


class REPLError(Base):
    pass


class REPLUnexpectedResult(REPLError):
    pass


class REPLTimeout(REPLError):
    pass
