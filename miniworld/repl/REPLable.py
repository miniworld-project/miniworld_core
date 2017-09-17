from miniworld import config
from miniworld.log import get_logger, get_file_handler
from miniworld.util import NetUtil
from miniworld.repl.CommandRunner import CommandRunner

__author__ = 'Nils Schmidt'


class REPLable(object):

    '''
    Offers read-evaluate-print-loop functionality for classes
    which perform operations on a unix domain socket.

    Moreover it enables an interactive REPL (see :py:class:`.REPL`)
    NOTE: the class needs further adoptions to handle a new :py:class:`.REPLable` object

    Attributes
    ----------
    path_uds_socket : str
        The path to unix domain socket.
    verbose_logger : logging.Logger if debug mode else None
        Logger for verbose stuff. Only used in debug mode, because it may slow down.
    '''

    ############################################
    # Set these variables in a subclass
    ############################################

    def __init__(self):
        self.path_uds_socket = None

        name = self.get_verbose_logger_path()
        self.verbose_logger = get_logger('verbose_%s' % name, handlers=[get_file_handler(name)]) if config.is_debug() else None

    ############################################
    # Implement these methods
    ############################################

    def render_script_from_flo(self, flo, **kwargs):
        '''
        Render the script from the file-like-object.
        This methods enables a subclass to inject some variables such as the ip addr or the node id.

        Returns
        -------
        str
        '''
        flo.seek(0)
        return flo.read()

    ############################################
    # UDS stuff
    ############################################

    def wait_until_uds_reachable(self, return_sock=False):
        ''' Wait until qemu is reachable via its unix domain socket.

        Parameters
        ----------
        return_sock: bool, optional (default is False)
            Return the socket.

        Returns
        -------
        socket
            The socket if `return_sock` else None. Remember to close the socket!
        '''
        self.nlog.debug("waiting until %s uds is reachable!", self.path_uds_socket)
        return NetUtil.wait_until_uds_reachable(self.path_uds_socket, return_sock=return_sock)

    ############################################
    # Command execution
    ############################################

    def run_commands_eager_check_ret_val(self, *args, **kwargs):
        '''
        Overwrite this method to provide a way of checking the return values of commands executed in the REPL.
        '''

        raise NotImplementedError

    def run_commands_eager(self, *args, **kwargs):
        '''
        Same as :py:meth:`.run_commands` but with eager evaluation (no generator).

        Returns
        -------
        str
            Output of the commands
        '''
        result = []
        for output in self.run_commands(*args, **kwargs):
            result.append(output)
        # skip socket
        return '\n'.join(result)

    def run_commands(self, *args, **kwargs):
        '''
        Run commands lazily from `flo` on the REPL.

        Lazy means: Run the command and return the socket as well as the results via a generator.
        Important: You have to evaluate the generator in order to execute all commands.
        The first item, is the socket which is connected to the unix domain socket.
        Because this method is blocking (on the uds socket) while executing the commands, one has the possibility to
        close the uds connection prematurely.

        For the documentation of the parameters, see the constructor of :py:class:`.CommandRunner`.

        '''
        timeout = kwargs.get("timeout") or config.get_repl_timeout()
        if "timeout" in kwargs:
            del kwargs["timeout"]

        cr = CommandRunner(self, timeout, *args, **kwargs)()
        for idx, res in enumerate(cr):
            # skip sock
            if idx == 1:
                yield res

    def run_commands_get_socket(self, *args, **kwargs):
        '''
        Same as :py:meth:`.run_commands` but do not throw the socket away, which is used for the REPL.
        '''
        timeout = config.get_repl_timeout()
        return CommandRunner(self, timeout, *args, **kwargs)()

    ############################################
    # Misc
    ############################################

    def get_verbose_logger_path(self):
        return "%s_repl_%s" % (self.__class__.__name__, self.id)
