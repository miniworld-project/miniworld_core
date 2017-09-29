import curses
import json
from itertools import imap, repeat
import progressbar
from miniworld.management.events.TerminalWriter import TerminalWriter
from miniworld.model.events.MyEventSystem import MyEventSystem

INFOBAR_PADDING_VERTICAL = 2

EVENT_OVERALL_PROGRESS = "Overall Progress"

event_length = 25


curses_ok = False
try:
    from blessings import Terminal  # noqa
    curses_ok = True
except curses.error:
    pass


class CLIEventDisplay:

    """
    CLI-based view for the :py:class:`.EventSystem`.
    Used a progressbar to display the progress of each event as well as the overall progress.
    For terminals that don't support it, the progress is prettyprinted as json to the terminal.
    """

    def __init__(self):
        """
        Parameters
        ----------
        pbars: dict<str, ProgressBar>
            Contains for each event a progressbar.
        """
        self.pbars = {}
        self.info_writer = None
        self.progress_gen = self.progress_gen()

    def create_progress_bar(self, event):
        """
        Create a :py:class:`.ProgressBar` for the `event` if none exists yet.
        Otherwise return the bar.

        Parameters
        ----------
        event : str

        Returns
        -------
        bool, ProgressBar.
            If the progressbar is newly created, the progressbar object.
        """
        if event not in self.pbars:

            def get_shared_widgets(event_name):
                event_name = event_name.ljust(event_length)[:event_length]
                return [event_name, ': ', progressbar.Percentage(), ' ']

            widgets = get_shared_widgets(event) + [progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', progressbar.ETA()]

            if event == MyEventSystem.EVENT_TOTAL_PROGRESS:
                widgets = get_shared_widgets(EVENT_OVERALL_PROGRESS) + [progressbar.Bar('>'), progressbar.ReverseBar('<'), ' ', progressbar.ETA()]

            pbar = progressbar.ProgressBar(fd=TerminalWriter(0, idx=self.get_progressbar_idx()), widgets=widgets, maxval=1.0).start()
            self.pbars[event] = pbar

            return True, pbar

        return False, self.pbars[event]

    def get_progressbar_idx(self):
        return len(self.pbars)

    @staticmethod
    def is_finished(progess_dict):
        """
        Check if all events of the `progess_dict` are finished (value: 1).

        Parameters
        ----------
        progess_dict: dict<str, float>

        Returns
        -------
        bool
        """
        return all(imap(lambda x: x == 1, progess_dict.values()))

    def progress_gen(self):
        for repeated_elm in repeat('|/-\\'):
            for c in repeated_elm:
                yield c

    def print_progress(self, progress_dict):
        """
        Print the progress for each event of `progess_dict`.

        Parameters
        ----------
        progress_dict: dict<str, float>
        """

        if curses_ok:
            # iterate over events and progress
            for event, progress in progress_dict.items():

                # create a bar if none exists yet
                created, pbar = self.create_progress_bar(event)

                # finish the bar if the event finished
                if progress == 1.0:
                    if not pbar.finished:
                        # update last time
                        pbar.update(progress)
                        pbar.finish()
                else:

                    # start the newly created bar
                    if created:
                        pbar.start()

                    # update not-yet finished event
                    pbar.update(progress)

            if self.info_writer is None:
                self.info_writer = TerminalWriter(0, idx=self.get_progressbar_idx() + INFOBAR_PADDING_VERTICAL)
            msg = 'Scenario starting: %s' % next(self.progress_gen)
            self.info_writer.write(msg)
        else:
            print(json.dumps(progress_dict, indent=4))
