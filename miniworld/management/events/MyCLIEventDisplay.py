from collections import OrderedDict
from threading import Thread

from miniworld.management.events.CLIEventDisplay import CLIEventDisplay


class MyCLIEventDisplay(CLIEventDisplay):

    def __init__(self, event_system, *args, **kwargs):
        """
        Automated version :py:class:`.CLIEventDisplay`.
        Updated the progress in a while-loop.

        Parameters
        ----------
        event_system
        """
        super(MyCLIEventDisplay, self).__init__(*args, **kwargs)
        self.event_system = event_system
        self.progress_thread = None

    def start_progress_thread(self):

        def loop():
            while True:
                progress_dict = OrderedDict(self.event_system.get_progress(asc=False))
                self.print_progress(progress_dict)

        self.progress_thread = Thread(target=loop)
        self.progress_thread.daemon = True
        self.progress_thread.start()


if __name__ == '__main__':
    from miniworld.management.events.MyCLIEventDisplay import MyCLIEventDisplay
    from miniworld.model.events.MyEventSystem import MyEventSystem
    import time

    es = MyEventSystem()
    cli_display = MyCLIEventDisplay(es)
    cli_display.start_progress_thread()

    def example_1():
        # context manager
        with es.event_init(es.EVENT_VM_BOOT) as e:

            with es.event_init(es.EVENT_NETWORK_BACKEND_SETUP) as e2:
                e2.update(["1"], 0.1)
            print("finishing ...")

            for i in range(10):
                time.sleep(0.2)
                e.update(["1"], 0.1 * i)
                e.update(["2"], 0.1 * i)
                e.update(["3"], 0.05 * i)

            time.sleep(1)
            print("finishing ...")

    def example_2():
        # neither do init nor finish
        with es.event_init(es.EVENT_VM_BOOT) as e:
            for i in range(10):
                time.sleep(0.2)
                # update all registered nodes
                e.update_all(0.01, add=True)

            time.sleep(1)
            print("finishing ...")

    example_1()
    example_2()

    time.sleep(100)
