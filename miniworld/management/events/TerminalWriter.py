
import curses

curses_ok = False

try:
    from blessings import Terminal
    term = Terminal()

    print(term.enter_fullscreen)
    curses_ok = True
except curses.error:
    pass

class TerminalWriter:
    """Create an object with a write method that writes to a
    specific place on the screen, defined at instantiation.

    This is the glue between blessings and progressbar.
    Starts writing the text from the bottom of the screen.
    Each writer has its own line.
    """
    def __init__(self, x_location, idx):
        """
        Parameters
        ----------
        x_location : int
            The x location.
        idx: int
            Higher index means higher on the terminal.
            0 is the last line of the terminal.
        """
        self.x_location = x_location
        self.idx = idx

    def write(self, string):
        '''
        Write a `string` to the terminal.
         Use `blessings` if available, otherwise print to stdout.

        Parameters
        ----------
        string : string
        '''
        msg = string
        if curses_ok:
            # clear line
            with term.location(self.x_location, 0):
                print(" " * term.width)

            # print line
            with term.location(self.x_location, term.height - self.idx - 2):
                print(msg)
        # no terminal support :/ e.g. IDE
        else:
            print(msg)
