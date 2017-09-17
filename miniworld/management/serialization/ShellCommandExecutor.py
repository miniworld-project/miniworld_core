import collections
from collections import defaultdict
from concurrent import futures
from multiprocessing import cpu_count

from ordered_set import OrderedSet

from miniworld.model.singletons.Resetable import Resetable
from miniworld.model.singletons.Singletons import singletons


class ShellCommandSerializer(object, Resetable):

    def __init__(self, name):
        """

        Parameters
        ----------
        name : str
        shell_command_args : OrderedSet<(str, str, str)>
        shell_commands : set<str>
        """
        self.name = name
        self.reset()

    def reset(self):
        self.shell_command_args = OrderedSet()
        self.__uniq_shell_commands = set()

    def get_shell_commands(self):
        return [x[1] for x in self.shell_command_args]

    def add_command(self, id, cmd, prefixes):
        prefixes = tuple(prefixes)
        if cmd not in self.__uniq_shell_commands:
            shell_command_arg = (id, cmd, prefixes)
            self.__uniq_shell_commands.add(cmd)
            self.shell_command_args.add(shell_command_arg)

    def run_commands(self, max_workers=None):
        if max_workers is None:
            max_workers = cpu_count()

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(lambda x: singletons.self.shell_helper.run_shell(*x), self.shell_command_args)


class ShellCommandExecutor(object, Resetable):
    """
    Examples
    --------
    >>> sce=ShellCommandExecutor()
    >>> sce.set_event_order("bridge", ["bridge_add", "bridge_set_hub", "bridge_up", "bridge_add_if"])
    >>> sce.add_command("bridge", "bridge_add_if", "e.g 1", "brctl addif br_foobar eth0", ["bridge"])
    >>> sce.add_command("bridge", "bridge_add", "e.g 1", "brctl addbr br_foobar", ["bridge"])
    Runs 'brctl addbr' before 'brctl addif'
    >>> sce.run_commands()

    """

    def __init__(self):
        """
        Parameters
        ----------

        serializable_events_for_id : dict<str, list<str>>
        shellcommandserializer_for_event_order_id : EventOrder
        event_order_id_order : list<str>
        """
        self.reset()

    def __str__(self):
        res = "Shell commands for network provisioning: "

        for (event_order_id, serializable_event), parallelizable_command_list in self.get_serialized_commands_per_event_order():
            res += "\n#Parallelizable commands for: %s, %s:\n" % (event_order_id, serializable_event)
            res += '\n'.join(parallelizable_command_list)
            res += "\n"

        return res

    def reset(self):
        self.serializable_events_for_id = {}
        self.shellcommandserializer_for_event_order_id = defaultdict(EventOrder)
        self.event_order_id_order = []

    def get_serialized_commands_event(self, event_order_id, event):
        """

        Parameters
        ----------
        event_order_id
        event

        Returns
        -------

        """
        scs = self.shellcommandserializer_for_event_order_id[event_order_id][event]
        return scs.get_shell_commands()

    def get_serialized_commands_all(self):
        res = []
        for (event_order_id, serializable_event), parallelizable_command_list in self.get_serialized_commands_per_event_order():
            res.extend(parallelizable_command_list)
        return res

    def get_serialized_commands_per_event_order(self):
        """

        Generator
        --------
        One list per `event_order_id`
            ((str, str), list<str>)
        """

        for event_order_id in self.event_order_id_order:
            serializable_event_order = self.serializable_events_for_id[event_order_id]

            for serializable_event in serializable_event_order:
                yield (event_order_id, serializable_event), self.get_serialized_commands_event(event_order_id, serializable_event)

    def run_commands(self, max_workers=None, events_order=None):
        """

        Parameters
        ----------
        max_workers
        events_order : list<str>
            List of events to filter for. E.g. "bridge".

        Returns
        -------

        """
        if events_order is None:
            events_order = self.event_order_id_order

        for event_order_id in self.event_order_id_order:

            if event_order_id not in events_order:
                continue

            serializable_event_order = self.serializable_events_for_id[event_order_id]

            for serializable_event in serializable_event_order:
                scs = self.shellcommandserializer_for_event_order_id[event_order_id][serializable_event]
                scs.run_commands(max_workers=max_workers)

    def set_event_order(self, event_order_id, event_order):
        self.serializable_events_for_id[event_order_id] = event_order

    def get_serializable_event_order(self, event_order_id):
        return self.serializable_events_for_id[event_order_id]

    def add_command(self, event_order_id, serializable_event,
                    id, cmd, prefixes):

        scs = self.shellcommandserializer_for_event_order_id[event_order_id][serializable_event]
        if scs is None:
            self.shellcommandserializer_for_event_order_id[event_order_id][serializable_event] = scs = ShellCommandSerializer(serializable_event)
        scs.add_command(id, cmd, prefixes)

    def set_event_super_order(self, event_order_id_order):
        self.event_order_id_order = event_order_id_order


class EventOrder(collections.UserDict):
    """
    Attributes
    -----------
    data : dict<str, ShellCommandSerializer>
    """

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            # apply default value
            self.data[key] = ShellCommandSerializer(key)
            return self.data[key]


if __name__ == '__main__':
    sce = ShellCommandExecutor()
    sce.set_event_order("bridge", ["bridge_add", "bridge_set_hub", "bridge_up", "bridge_add_if"])
    sce.add_command("bridge", "bridge_add_if", "e.g 1", "brctl addif br_foobar eth0", ["bridge"])
    sce.add_command("bridge", "bridge_add_if", "e.g 1", "brctl addif br_foobar eth1", ["bridge"])
    sce.add_command("bridge", "bridge_add", "e.g 1", "brctl addbr br_foobar", ["bridge"])

    sce.set_event_order("connection", ["connection_mod"])
    sce.add_command("connection", "connection_mod", "e.g 1", "ifconfig eth0 up", ["connection"])
    # Runs 'brctl addbr' before 'brctl addif'

    #sce.set_event_order_id_order(["bridge", "connection"])
    sce.set_event_super_order(["connection", "bridge"])
    # sce.run_commands()
    print(list(sce.get_serialized_commands_per_event_order()))
    # sce.run_commands()
