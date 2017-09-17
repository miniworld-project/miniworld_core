from pprint import pformat
from subprocess import check_output

from pyroute2.ipdb.exceptions import CreateException
from pyroute2.netlink import NetlinkError

from miniworld.errors import NetworkBackendStartError, NetworkBackendBridgedBridgeError
from miniworld.model.network.backends.bridged.Bridge import Bridge
from miniworld.model.singletons.Singletons import singletons


def BridgePyroute2():
    class BridgePyroute2(Bridge):

        """
        Attributes
        ----------
        id : str
            Name of the bridge.
        bridge: pyroute2.ipdb.interface.Interface
        """

        def _start(self, bridge_dev_name=None, switch=False):
            self.bridge_dev_name = bridge_dev_name

            try:
                self.bridge = singletons.network_backend.get_ipdb().create(kind='bridge', ifname=self.bridge_dev_name)
                # get_ipdb_logger().info("%s = get_ipdb_singleton().create(kind='bridge', ifname='%s')" % (self.bridge_dev_name, self.bridge_dev_name))
                # See Also: https://github.com/svinota/pyroute2/issues/254
                self.bridge.set_br_ageing_time(0)
                #get_ipdb_logger().info("%s.set_br_ageing_time(0)" % self.bridge_dev_name)

            except (NetlinkError, CreateException) as e:
                raise NetworkBackendStartError("Could not create the bridge with name '%s' in hub mode!" % self.bridge_dev_name, caused_by=e)

        def add_if(self, _if_name, if_up=True):
            try:
                tap_dev = singletons.network_backend.get_ipdb().interfaces[_if_name]
                tap_dev_name = tap_dev['ifname']
                if if_up:
                    if not singletons.network_backend.connection_book_keeper.interface_states[tap_dev_name]:
                        tap_dev.up()
                        #get_ipdb_logger().info("%s = get_ipdb_singleton().interfaces['%s']" % (tap_dev_name, tap_dev_name))
                        #get_ipdb_logger().info("%s.up()" %tap_dev_name)
                        # remember that the device is up (or down)
                        singletons.network_backend.connection_book_keeper.interface_states.toggle_state(tap_dev_name, if_up)

                self.bridge.up()
                #get_ipdb_logger().info("%s.up()" % self.bridge_dev_name)
                self.bridge.add_port(tap_dev['index'])
                #get_ipdb_logger().info("%s.add_port(%s['index'])" % (self.bridge_dev_name, tap_dev_name))

            except (AttributeError, KeyError) as e:
                raise NetworkBackendBridgedBridgeError("""Could not add interface '%s' to bridge '%s'
                Bridge dump:
                %s
                Interface dump:
                %s
                Used tap devices:
                %s
                """ % (_if_name, self, check_output(["brctl", "show"]), pformat(Bridge.get_interfaces()),
                       pformat(singletons.network_backend._tap_id_mapping)), caused_by=e)

    #     def reset(self):
    #         """
    #         Raises
    #         ------
    #         NetworkBackendErrorReset
    #
    #         Returns
    #         -------
    #
    #         """
    #         try:
    #             if self.bridge_dev_name:
    #                 # use pyroute2 since otherwise the cache may not be in sync
    #                 self.bridge.remove()
    #                 self.bridge.commit()
    #
    #         except Exception as e:
    #             raise NetworkBackendErrorReset("""Could not shutdown the bridge '%s'
    # Interface dump:
    # %s
    # """ % (self, pformat(self.get_interfaces())), caused_by=e)

    return BridgePyroute2


def BridgePyroute2IPRoute():
    class BridgePyroute2IPRoute(Bridge):

        """
        Attributes
        ----------
        id : str
            Name of the bridge.
        bridge: pyroute2.ipdb.interface.Interface
        """

        def _start(self, bridge_dev_name=None, switch=False):
            self.bridge_dev_name = bridge_dev_name

            try:
                singletons.network_backend.p_bridges.add(self.bridge_dev_name)

                # TODO: hub
                #singletons.network_backend.get_batch_object().link("set", index=singletons.network_backend.get_iface_idx(self.bridge_dev_name), ageing_time=0)
                # self.bridge.set_br_ageing_time(0)

            # TODO: check exceptions
            except (NetlinkError, CreateException) as e:
                raise NetworkBackendStartError("Could not create the bridge with name '%s' in hub mode!" % self.bridge_dev_name, caused_by=e)

        def add_if(self, _if_name, if_up=True):
            try:
                singletons.network_backend.p_links_add_bridge[self.bridge_dev_name].append(_if_name)
                if if_up:
                    if not singletons.network_backend.connection_book_keeper.interface_states[_if_name]:
                        singletons.network_backend.p_links_up.add(_if_name)

                else:
                    if singletons.network_backend.connection_book_keeper.interface_states[_if_name]:
                        singletons.network_backend.p_links_down.add(_if_name)

                # remember that the device is up (or down)
                singletons.network_backend.connection_book_keeper.interface_states.toggle_state(_if_name, if_up)

            # TODO: check exceptions
            except (AttributeError, KeyError) as e:
                raise NetworkBackendBridgedBridgeError("""Could not add interface '%s' to bridge '%s'
                Bridge dump:
                %s
                Interface dump:
                %s
                Used tap devices:
                %s
                """ % (_if_name, self, check_output(["brctl", "show"]), pformat(Bridge.get_interfaces()),
                       pformat(singletons.network_backend._tap_id_mapping)), caused_by=e)

    return BridgePyroute2IPRoute
