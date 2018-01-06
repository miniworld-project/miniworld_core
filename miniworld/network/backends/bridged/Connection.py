import subprocess
from collections import defaultdict

from ordered_set import OrderedSet
from typing import Dict

from miniworld.impairment import LinkQualityConstants
from miniworld.impairment.bridged.NetEm import NetEm
from miniworld.network.connection import AbstractConnection, ConnectionServiceBase
from miniworld.singletons import singletons
from miniworld.model.domain.connection import Connection as DomainConnection

__author__ = 'Nils Schmidt'


def get_superclass_dynamic():
    assert singletons.scenario_config.is_network_backend_bridged_connection_mode_set()

    import miniworld.network.backends.bridged.singledevice.ConnectionEbtables

    return miniworld.network.backends.bridged.singledevice.ConnectionEbtables.ConnectionEbtables() if singletons.scenario_config.is_network_backend_bridged_connection_mode_single() else miniworld.network.backends.bridged.multidevice.ConnectionMultiBridges.ConnectionMultiBridges()


def ConnectionDummy():
    class ConnectionService(ConnectionServiceBase):
        """

        """

        EVENT_ROOT = "connection"
        EVENT_CONN_STATE_CHANGE = "conn_state_change"
        EVENT_LINK_SHAPE_ADD_CLASS = "link_shape_add_class"
        EVENT_LINK_SHAPE_ADD_QDISC = "link_shape_add_child"
        EVENT_LINK_SHAPE_ADD_FILTER = "link_shape_add_filter"
        EVENT_ORDER = OrderedSet([EVENT_CONN_STATE_CHANGE, EVENT_LINK_SHAPE_ADD_QDISC, EVENT_LINK_SHAPE_ADD_CLASS,
                                  EVENT_LINK_SHAPE_ADD_FILTER])

        PREFIXES = ["connection"]

        shaped_ifaces = defaultdict(lambda: False)
        cleanup_commands = set()

        def __init__(self):
            super().__init__()
            self._logger = singletons.logger_factory.get_logger(self)
            # TODO: just for prototyping
            self.id = 100000

        # TODO: INTERFACE FOR ShellCommandSerializer STUFF?
        # COMMON VARIABLES AND THIS METHOD
        def add_shell_command(self, event, cmd):
            singletons.network_backend.shell_command_executor.add_command(self.EVENT_ROOT, event, self.id, cmd,
                                                                          self.PREFIXES)

        def run(self, cmd):
            return singletons.shell_helper.run_shell(self.id, cmd, prefixes=["tc"])

        ###############################################
        # Subclassed methods of AbstractConnection
        ###############################################

        def start(self, connection: DomainConnection):
            pass

        ###############################################
        # Link Quality
        ###############################################

        def adjust_link_quality(self, connection: DomainConnection, link_quality_dict):
            """

            Parameters
            ----------
            link_quality_dict

            Returns
            -------
            """

            # assumes only equal interfaces can be connected to each other
            bandwidth = link_quality_dict.get(LinkQualityConstants.LINK_QUALITY_KEY_BANDWIDTH)

            self._logger.info("adjusting link quality ...")

            if bandwidth is not None:
                is_hubwifi = connection.connection_type == AbstractConnection.ConnectionType.central
                _, _, emu_node, if_emu_node = self._get_central_node(connection=connection)

                connection_id = connection._id
                if is_hubwifi:
                    tap_dev_name = singletons.network_backend.get_tap_name(emu_node._id, if_emu_node)
                    self._shape_device(tap_dev_name, connection_id, link_quality_dict)
                else:
                    # get tap device names
                    tap_x = singletons.network_backend.get_tap_name(connection.emulation_node_x._id, connection.interface_x)
                    tap_y = singletons.network_backend.get_tap_name(connection.emulation_node_y._id, connection.interface_y)

                    # traffic shape downlinks
                    # because each device is connected to a linux bridge,
                    # the connection between the two hosts is shaped in down- and uplink.

                    # TODO: move to iproute2 connection!
                    if connection.is_remote_conn:
                        remote_node, if_remote_node, local_emu_node, if_local_emu_node = self._get_remote_node(connection=connection)
                        tap_local = singletons.network_backend.get_tap_name(local_emu_node._id, if_local_emu_node)
                        # tunnel_dev = singletons.network_backend.get_tunnel_name(remote_node._id, local_emu_node._id)
                        self._shape_device(tap_local, connection_id, link_quality_dict)
                        # NOTE: this happens at the other server!
                        # self.shape_device(tap_remote, connection_id, link_quality_dict)
                    else:
                        self._shape_device(tap_x, connection_id, link_quality_dict)
                        self._shape_device(tap_y, connection_id, link_quality_dict)

        def _shape_device(self, dev_name, connection_id, link_quality_dict):
            """
            Parameters
            ----------
            dev_name : str
            connection_id : str
            rate : int

            tc qdisc add dev $DEV root handle 1:0 htb default 12
            tc class add dev $DEV parent 1:0 classid 1:1 htb rate 190kbit ceil 190kbit
            tc class add dev $DEV parent 1:1 classid 1:12 htb rate 100kbit ceil 190kbit prio 2
            """
            connection_id += 1
            assert connection_id > 0, 'causes problems with `tc` command'
            rate = link_quality_dict.get(LinkQualityConstants.LINK_QUALITY_KEY_BANDWIDTH)

            if rate is not None:

                # add root
                default_class = self._get_default_class()
                if default_class:
                    default_class = "default %s" % default_class

                if not self.shaped_ifaces[dev_name]:
                    postfix = ' htb {}'.format(default_class)
                    self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_QDISC,
                                           # TODO: ADD/REMOVE default 1
                                           "tc qdisc replace dev {} root handle 1:0{}".format(dev_name, postfix))
                self.shaped_ifaces[dev_name] = True

                # add first and only class, use htb shaping algorithm
                self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_CLASS,
                                       "tc class replace dev {} parent 1:0 classid 1:{id} htb rate {rate}kbit".format(
                                           dev_name, rate=rate, id=connection_id))

                # TODO: DOC
                netem_command = "tc qdisc replace dev {dev_name} parent 1:{id} handle {id}0: netem".format(
                    dev_name=dev_name, id=connection_id)

                def build_netem_options():
                    netem_options = []

                    def build_opt(key):
                        opt = link_quality_dict.get(key)
                        if opt:
                            netem_options.append("%s %s" % (key, opt))

                    for key in NetEm.NETEM_KEYS:
                        build_opt(key)

                    return ' '.join(netem_options)

                netem_command += ' {}'.format(build_netem_options())
                self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_CLASS, netem_command)
                self._add_filter_cmd(dev_name, connection_id)
                self.add_cleanup(dev_name)

            else:
                self._logger.info("not shaping device %s", dev_name)

        @staticmethod
        def get_connection_id(tap_x, tap_y):
            raise NotImplementedError

        def _add_filter_cmd(self, dev_name, connection_id):
            raise NotImplementedError

        def _get_default_class(self):
            raise NotImplementedError

        ###############################################
        ###
        ###############################################

        def link_up(self, connection: DomainConnection, link_quality_dict: Dict):
            self.set_connection_state(connection=connection, up=True)

        def link_down(self, connection: DomainConnection, link_quality_dict: Dict):
            self.set_connection_state(connection=connection, up=False)

        ###############################################
        ###
        ###############################################

        # TODO: RENAME!
        def set_connection_state(self, connection: DomainConnection, up=True):
            """

            Parameters
            ----------
            up : bool, optional (default is False)
                Set the device(s) up. Otherwise down.

            Returns
            -------

            """
            is_hubwifi = connection.connection_type == AbstractConnection.ConnectionType.central

            if is_hubwifi:
                emu_node, if_emu_node, emu_node_2, if_emu_node_2 = self._get_central_node()
                tap_dev_name = singletons.network_backend.get_tap_name(emu_node._id, if_emu_node)
                tap_central_node = emu_node_2.switch.id
                self.tap_link_up_central(tap_dev_name, tap_central_node, up=up)
            elif connection.is_remote_conn:

                remote_node, if_remote_node, local_emu_node, if_local_emu_node = self._get_remote_node()

                # always produce the same dev name => sort nodes by id
                node_id_1, node_id_2 = (remote_node._id, local_emu_node._id) if remote_node._id < local_emu_node._id else (
                    local_emu_node._id, remote_node._id)
                tunnel_dev_name = singletons.network_backend.get_tunnel_name(node_id_1, node_id_2)
                tap_local = singletons.network_backend.get_tap_name(local_emu_node.i_d, if_local_emu_node)

                self.tap_link_up_remote(tunnel_dev_name, tap_local, up=up)
                self.tap_link_up_remote(tap_local, tunnel_dev_name, up=up)
            else:
                # get tap device names
                tap_x = singletons.network_backend.get_tap_name(connection.emulation_node_x._id, connection.interface_x)
                tap_y = singletons.network_backend.get_tap_name(connection.emulation_node_y._id, connection.interface_y)

                self.tap_link_up(connection, tap_x, tap_y, up=up)
                self.tap_link_up(connection, tap_y, tap_x, up=up)

        def reset(self):
            self.shaped_ifaces = defaultdict(lambda: False)

            # we stored the commands since the tap dev mapping is already reseted at this point
            for cleanup_cmd in self.cleanup_commands:
                try:
                    self.run(cleanup_cmd)
                except subprocess.CalledProcessError as e:
                    self._logger.exception(e)

            self.cleanup_commands = set()

        def add_cleanup(self, dev_name):
            self.cleanup_commands.add('tc qdisc del dev {dev_name} root'.format(dev_name=dev_name))

        ###############################################
        # Subclass for custom execution mode
        # like iproute2 vs. pyroute2. vs brctl
        ###############################################

        # # TODO: #84 move to NetworkBackendBridgedMultiDevice
        def tap_link_up(self, connection, tap_x, tap_y, up=True):
            raise NotImplementedError

        def tap_link_up_central(self, connection, tap_x, tap_y, up=True):
            raise NotImplementedError

        def tap_link_up_remote(self, connection, tap_x, tap_y, up=True):
            raise NotImplementedError

        @staticmethod
        def _get_central_node(connection: DomainConnection):
            return singletons.simulation_manager.get_central_node(connection.emulation_node_x, connection.emulation_node_y,
                                                                  connection.interface_x, connection.interface_y)

        @staticmethod
        def _get_remote_node(connection: DomainConnection):
            return singletons.simulation_manager.get_remote_node(connection.emulation_node_x, connection.emulation_node_y,
                                                                 connection.interface_x, connection.interface_y)

    return ConnectionService


def Connection():
    class Connection(get_superclass_dynamic()):  # choose connection for connection mode
        pass

    return Connection
