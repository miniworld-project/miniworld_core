__author__ = 'Nils Schmidt'

class ShellCmdWrapper:

    '''
    Attributes
    ----------
    shell_prefix : str, optional ( default is the class name )
        Name of the shell command to be wrapped.
    process : subprocess32.Popen
    '''
    def __init__(self):
        # TODO: #2: DOC
        super(ShellCmdWrapper, self).__init__()
        self.shell_prefix = None
        self.process = None

    def start(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def shell_prefix(self):
        return str(self.__class__.__name__)