import collections
import math
from collections import OrderedDict
from concurrent import futures

from ordered_set import OrderedSet

from miniworld.model.ResetableInterface import ResetableInterface
from miniworld.singletons import singletons
from miniworld.util import ConcurrencyUtil


class ShellCommandSerializer(ResetableInterface):
    """
    This class can serialize commands into a given order and prevent duplicate commands!
    A group contains a list of events that belong to it. The events have an order.
    Adding commands to the events in the group keeps the order of the commands (sorted by event order).

    The purpose of this class is to ensure that commands are executed in a order which is independent of the insertion order.

    The commands for each event, are executed in parallel.
    Therefore, commands which shall be executed in a special order, should be splitted into events so that the commands in the event can be executed in parallel.

    Moreover, one has also to define the order of the groups.
    Look at the example below:
    - There are 3 groups: bridge, connection and new_event_group.
    - The creation of a bridge has to be done before operations on it can be done.
      Therefore we set the group order so that all bridge commands are executed before any operations are done on the linked
    - Moreover, there is also an order inside the events: ["bridge_add", "bridge_set_hub", "bridge_up", "bridge_add_if"]

    Examples
    --------
    >>> scs=ShellCommandSerializer()

    >>> scs.set_event_order("bridge", ["bridge_add", "bridge_set_hub", "bridge_up", "bridge_add_if"]) # <- event_order
    >>> # naming:
    >>> #                        ^        ^
    >>> #                    group/tag  event
    >>> scs.add_command("bridge", "bridge_add_if", "e.g 1", "brctl addif br_foobar eth0", ["bridge"])
    >>> scs.add_command("bridge", "bridge_add_if", "e.g 1", "brctl addif br_foobar eth1", ["bridge"])
    >>> scs.add_command("bridge", "bridge_add", "e.g 1", "brctl addbr br_foobar", ["bridge"])

    >>> scs.set_event_order("connection", ["state_change"])
    >>> scs.add_command("connection", "state_change", "e.g 1", "ifconfig eth0 up", ["connection"])

    >>> scs.set_group_order(["bridge", "connection"])
    >>> print scs.get_all_commands()
    ['brctl addbr br_foobar', 'brctl addif br_foobar eth0', 'brctl addif br_foobar eth1', 'ifconfig eth0 up']

    >>> # add an event group inclusive the event_order later
    >>> scs.add_group("new_event_group")
    >>> scs.set_event_order("new_event_group", ["new_event_1", "new_event_2"])


    >>> print scs.mapping_group_to_event_order_to_cs
    {'new_event_group': Event2CommandStoreMapping([('new_event_1', CommandStore([])), ('new_event_2', CommandStore([]))]), 'bridge': Event2CommandStoreMapping([('bridge_add', CommandStore(['brctl addbr br_foobar'])), ('bridge_set_hub', CommandStore([])), ('bridge_up', CommandStore([])), ('bridge_add_if', CommandStore(['brctl addif br_foobar eth0', 'brctl addif br_foobar eth1']))]), 'connection': Event2CommandStoreMapping([('state_change', CommandStore(['ifconfig eth0 up']))])}
    >>> # Run the commands
    >>> sce.run_commands()
    ...

    """

    def __init__(self):
        """
        Parameters
        ----------
        mapping_group_to_event_order_to_cs : Group2EventMapping
        group_order : OrderedSet<str>
            Keeps the order of the groups.
            We intentionally do not use the order from the `mapping_group_to_event_order_to_cs`
            because the OrderedDict does not have the possibility to reorder the groups!
        """
        self.reset()

    def __str__(self):
        return str(self.mapping_group_to_event_order_to_cs)

    def __repr__(self):
        return repr(self.mapping_group_to_event_order_to_cs)

    def reset(self):
        self.mapping_group_to_event_order_to_cs = Group2EventMapping()
        self.group_order = OrderedSet()

    #########################################################
    # Add a command
    #########################################################

    def add_command(self, group, event,
                    id, cmd, prefixes):
        """

        Parameters
        ----------
        group : str
        event : str
        id : str
        cmd : str
        prefixes : iterable<str>

        Returns
        -------
        CommandStore
        """

        cs = self.mapping_group_to_event_order_to_cs[group][event]
        if cs is None:
            self.mapping_group_to_event_order_to_cs[group][event] = cs = CommandStore(event)
        cs.add_command(id, cmd, prefixes)

        return cs

    #########################################################
    # Set and get group order
    #########################################################

    def add_group(self, event):
        self.group_order.add(event)

    def set_group_order(self, event_order_id_order):
        """
        Set the group order.

        Parameters
        ----------
        event_order_id_order : iterable<str>
        """
        self.group_order = OrderedSet(event_order_id_order)

    #########################################################
    # Set and get event order
    #########################################################

    def set_event_order(self, group, event_order):
        """
        Set the order of events for a group.

        Parameters
        ----------
        group : str
        event_order : iterable<str>
        """

        # remember event order
        for event in event_order:
            self.mapping_group_to_event_order_to_cs[group][event]

    def get_event_order(self, group):
        return self.mapping_group_to_event_order[group]

    #########################################################
    # Get the commands ...
    #########################################################

    def get_commands_event(self, group, event):
        """
        Get all commands for the given `event` registered in the `group`.

        Parameters
        ----------
        group : str
        event : str

        Returns
        -------
        iterable<str>
        """
        cs = self.mapping_group_to_event_order_to_cs[group][event]
        return cs.get_shell_commands()

    def get_all_commands(self):
        """

        Returns
        -------
        list<str>
        """
        res = []
        for group in self.group_order:
            for event, command_store in self.mapping_group_to_event_order_to_cs[group].items():
                res.extend(command_store.get_shell_commands())

        return res

    def get_verbose_info(self):
        res = "#Shell commands for network provisioning: "
        for group in self.group_order:
            for event, command_store in self.mapping_group_to_event_order_to_cs[group].items():
                command_list = command_store.get_shell_commands()

                res += "\n#Parallelizable commands for: %s, %s:\n" % (group, event)
                res += '\n'.join(command_list)
                res += "\n"
        return res

    #########################################################
    # Run the commands ...
    #########################################################

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
            events_order = self.group_order

        # run over the groups
        for group in self.group_order:

            if group not in events_order:
                continue

            # get the event order inside of a group
            event_order = self.mapping_group_to_event_order_to_cs[group].get_event_order()

            for event in event_order:
                cs = self.mapping_group_to_event_order_to_cs[group][event]
                cs.run_commands(max_workers=max_workers)


class Group2EventMapping(collections.UserDict):
    """
    Stores for each group a :py:class:`.Event2CommandStoreMapping` which defines an event oder for the group.

    Attributes
    ----------
    data : dict<str, Event2CommandStoreMapping>
    """

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            # apply default value
            # NOTE: we need an ordered collection here to ensure the order of the events is correct
            self.data[key] = Event2CommandStoreMapping()
            return self.data[key]


class Event2CommandStoreMapping(OrderedDict):
    """
    Stores for each event a :py:class:`.CommandStore`.

    Attributes
    ----------
    data : dict<str, CommandStore>
    """

    def __getitem__(self, key):
        try:
            return super(Event2CommandStoreMapping, self).__getitem__(key)
        except KeyError:
            # apply default value
            self[key] = CommandStore(key)
            return super(Event2CommandStoreMapping, self).__getitem__(key)

    def get_event_order(self):
        return list(self.keys())


class CommandStore(ResetableInterface):

    def __init__(self, name):
        """
        Stores the commands for an event.
        All commands are considered to be executed in parallel.

        Parameters
        ----------
        name : str
        shell_command_args : OrderedSet<(str, str, str)>
        shell_commands : set<str>
        """
        self.name = name
        self.reset()

    def __str__(self):
        return str(self.get_shell_commands())

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self)

    def reset(self):
        self.shell_command_args = OrderedSet()
        self.__uniq_shell_commands = set()

    def get_shell_commands(self):
        return [x[1] for x in self.shell_command_args]

    @staticmethod
    def chunkIt(seq, num):
        avg = len(seq) / float(num)
        out = []
        last = 0.0

        while last < len(seq):
            out.append(seq[int(last):int(last + avg)])
            last += avg

        return out

    def get_one_shell_call_commands(self):
        """
        Shell commands as sh one-liner.

        Returns
        -------
        list<str>
        """
        commands = []
        MAX_ARG_STR_LEN = 131072

        shell_commands = self.get_shell_commands()

        # compress commands to one command with sh -c " cmd_1; ...; cmd_n"
        res = '; '.join(shell_commands)
        length = len(res) + len("sh -c ''")
        cnt_cmds = int(math.ceil(length * 1.0 / MAX_ARG_STR_LEN))

        # assume commands have equal length
        for commands_chunk in self.chunkIt(shell_commands, cnt_cmds):
            commands.append("sh -c '%s'" % '; '.join(commands_chunk))
        return commands

    def add_command(self, id, cmd, prefixes):
        """
        Add a command to the store and prevent duplicates!

        Parameters
        ----------
        id : str
        cmd : str
        prefixes : iterable<str>
        """
        prefixes = tuple(prefixes)
        # check for unique command
        if cmd not in self.__uniq_shell_commands:
            shell_command_arg = (id, cmd, prefixes)
            self.__uniq_shell_commands.add(cmd)
            self.shell_command_args.add(shell_command_arg)

    def run_commands(self, max_workers=None):
        """

        Parameters
        ----------
        max_workers

        Returns
        -------

        """
        if max_workers is None:
            max_workers = ConcurrencyUtil.cpu_count()

        if self.shell_command_args:
            def fun(*args, **kwargs):
                singletons.shell_helper.run_shell(*args[0], **kwargs)

            # run the commands in one shell call
            if singletons.scenario_config.is_network_backend_bridged_execution_mode_one_shell_call():
                _id, cmds, prefixes = self.shell_command_args[0][0], self.get_one_shell_call_commands(), self.shell_command_args[0][2]
                for cmd in cmds:
                    singletons.shell_helper.run_shell(_id, cmd, prefixes)
            # run the commands with multiple workers (can also be one worker if backend option is not set to parallel)
            elif singletons.scenario_config.is_network_backend_parallel():
                with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    executor.map(fun, self.shell_command_args)
            elif not singletons.scenario_config.is_network_backend_parallel():
                list(map(fun, self.shell_command_args))
