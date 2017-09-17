import subprocess
from collections import defaultdict

from ordered_set import OrderedSet

from miniworld import log
from miniworld.Scenario import scenario_config
from miniworld.model.network.backends.AbstractConnection import AbstractConnection
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import *
from miniworld.model.network.linkqualitymodels.LinkQualityModelRange import LinkQualityModelNetEm
from miniworld.model.singletons.Singletons import singletons
__author__ = 'Nils Schmidt'


def get_superclass_dynamic():
    assert scenario_config.is_network_backend_bridged_connection_mode_set()

    import miniworld.model.network.backends.bridged.multidevice.ConnectionMultiBridges
    import miniworld.model.network.backends.bridged.singledevice.ConnectionEbtables

    return miniworld.model.network.backends.bridged.singledevice.ConnectionEbtables.ConnectionEbtables() if scenario_config.is_network_backend_bridged_connection_mode_single() else miniworld.model.network.backends.bridged.multidevice.ConnectionMultiBridges.ConnectionMultiBridges()


def ConnectionDummy():
    class ConnectionDummy(AbstractConnection):
        """

        """

        EVENT_ROOT = "connection"
        EVENT_CONN_STATE_CHANGE = "conn_state_change"
        EVENT_LINK_SHAPE_ADD_CLASS = "link_shape_add_class"
        EVENT_LINK_SHAPE_ADD_QDISC = "link_shape_add_child"
        EVENT_LINK_SHAPE_ADD_FILTER = "link_shape_add_filter"
        EVENT_ORDER = OrderedSet([EVENT_CONN_STATE_CHANGE, EVENT_LINK_SHAPE_ADD_QDISC, EVENT_LINK_SHAPE_ADD_CLASS, EVENT_LINK_SHAPE_ADD_FILTER])

        PREFIXES = ["connection"]

        shaped_ifaces = defaultdict(lambda: False)
        cleanup_commands = set()

        # TODO: INTERFACE FOR ShellCommandSerializer STUFF?
        # COMMON VARIABLES AND THIS METHOD
        def add_shell_command(self, event, cmd):
            singletons.network_backend.shell_command_executor.add_command(self.EVENT_ROOT, event, self.id, cmd, self.PREFIXES)

        def run(self, cmd):
            return singletons.shell_helper.run_shell(self.id, cmd, prefixes=["tc"])

        def _has_mgmt_if(self):
            return self.interface

        ###############################################
        # Subclassed methods of AbstractConnection
        ###############################################

        # TODO: #54,#55, adjust doc
        # TODO: #54, #55: refactor!
        def start(self, start_activated=False):
            pass

        ###############################################
        # Link Quality
        ###############################################

        # TODO: implement adjustment with netem!
        def adjust_link_quality(self, link_quality_dict):
            """

            Parameters
            ----------
            link_quality_dict

            Returns
            -------
            """

            # assumes only equal interfaces can be connected to each other
            bandwidth = link_quality_dict.get(LINK_QUALITY_KEY_BANDWIDTH)

            self.nlog.info("adjusting link quality ...")

            if bandwidth is not None:
                is_hubwifi = self.connection_info.is_central
                _, _, emu_node, if_emu_node = self.get_central_node()

                connection_id = None
                if is_hubwifi:
                    tap_dev_name = singletons.network_backend.get_tap_name(emu_node.id, if_emu_node)
                    self.shape_device(tap_dev_name, connection_id, link_quality_dict)
                else:
                    # get tap device names
                    tap_x = singletons.network_backend.get_tap_name(self.emulation_node_x.id, self.interface_x)
                    tap_y = singletons.network_backend.get_tap_name(self.emulation_node_y.id, self.interface_y)
                    connection_id = self.get_connection_id(tap_x, tap_y)

                    # traffic shape downlinks
                    # because each device is connected to a linux bridge,
                    # the connection between the two hosts is shaped in down- and uplink.

                    # TODO: move to iproute2 connection!
                    if self.connection_info.is_remote_conn:
                        remote_node, if_remote_node, local_emu_node, if_local_emu_node = self.get_remote_node()
                        tap_local = singletons.network_backend.get_tap_name(local_emu_node.id, if_local_emu_node)
                        tunnel_dev = singletons.network_backend.get_tunnel_name(remote_node.id, local_emu_node.id)
                        connection_id = self.get_connection_id(tap_local, tunnel_dev)
                        self.shape_device(tap_local, connection_id, link_quality_dict)
                        # NOTE: this happens at the other server!
                        #self.shape_device(tap_remote, connection_id, link_quality_dict)
                    else:
                        self.shape_device(tap_x, connection_id, link_quality_dict)
                        self.shape_device(tap_y, connection_id, link_quality_dict)

        def shape_device(self, dev_name, connection_id, link_quality_dict):
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

            rate = link_quality_dict.get(LINK_QUALITY_KEY_BANDWIDTH)
            delay = link_quality_dict.get(LINK_QUALITY_KEY_DELAY)

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

                    for key in LinkQualityModelNetEm.NETEM_KEYS:
                        build_opt(key)

                    return ' '.join(netem_options)

                netem_command += ' {}'.format(build_netem_options())
                self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_CLASS, netem_command)
                self._add_filter_cmd(dev_name, connection_id)
                self.add_cleanup(dev_name)

            else:
                log.info("not shaping device %s", dev_name)

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

        # TODO: nearly same code as link_down!
        def link_up(self, link_quality_dict):
            self.set_connection_state(up=True)

        def link_down(self, link_quality_dict):
            self.set_connection_state(up=False)

        ###############################################
        ###
        ###############################################

        # TODO: RENAME!
        def set_connection_state(self, up=True):
            """

            Parameters
            ----------
            up : bool, optional (default is False)
                Set the device(s) up. Otherwise down.

            Returns
            -------

            """
            is_hubwifi = self.connection_info.is_central

            if is_hubwifi:
                emu_node, if_emu_node, emu_node_2, if_emu_node_2 = self.get_central_node()
                tap_dev_name = singletons.network_backend.get_tap_name(emu_node.id, if_emu_node)
                tap_central_node = emu_node_2.switch.id
                self.tap_link_up_central(tap_dev_name, tap_central_node, up=up)
            elif self.connection_info.is_remote_conn:

                remote_node, if_remote_node, local_emu_node, if_local_emu_node = self.get_remote_node()

                # always produce the same dev name => sort nodes by id
                node_id_1, node_id_2 = (remote_node.id, local_emu_node.id) if remote_node.id < local_emu_node.id else (local_emu_node.id, remote_node.id)
                tunnel_dev_name = singletons.network_backend.get_tunnel_name(node_id_1, node_id_2)
                tap_local = singletons.network_backend.get_tap_name(local_emu_node.id, if_local_emu_node)

                self.tap_link_up_remote(tunnel_dev_name, tap_local, up=up)
                self.tap_link_up_remote(tap_local, tunnel_dev_name, up=up)
            else:
                # get tap device names
                tap_x = singletons.network_backend.get_tap_name(self.emulation_node_x.id, self.interface_x)
                tap_y = singletons.network_backend.get_tap_name(self.emulation_node_y.id, self.interface_y)

                self.tap_link_up(tap_x, tap_y, up=up)
                self.tap_link_up(tap_y, tap_x, up=up)

        def reset(self):
            ConnectionDummy.shaped_ifaces = defaultdict(lambda: False)

            # we stored the commands since the tap dev mapping is already reseted at this point
            for cleanup_cmd in ConnectionDummy.cleanup_commands:
                try:
                    self.run(cleanup_cmd)
                except subprocess.CalledProcessError as e:
                    log.exception(e)

            ConnectionDummy.cleanup_commands = set()

        def add_cleanup(self, dev_name):
            self.cleanup_commands.add('tc qdisc del dev {dev_name} root'.format(dev_name=dev_name))

        ###############################################
        # Subclass for custom execution mode
        # like iproute2 vs. pyroute2. vs brctl
        ###############################################

        # # TODO: #84 move to NetworkBackendBridgedMultiDevice
        def tap_link_up(self, tap_x, tap_y, up=True):
            raise NotImplementedError

        def tap_link_up_central(self, tap_x, tap_y, up=True):
            raise NotImplementedError

        def tap_link_up_remote(self, tap_x, tap_y, up=True):
            raise NotImplementedError

    return ConnectionDummy


def Connection():
    class Connection(
        # choose connection for connection mode
            get_superclass_dynamic()):
        pass

    return Connection
