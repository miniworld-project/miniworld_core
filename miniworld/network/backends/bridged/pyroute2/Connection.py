from miniworld.errors import NetworkBackendConnectionError
from miniworld.network.backends.bridged.Connection import Connection
from miniworld.singletons import singletons


def ConnectionPyroute2():
    class ConnectionPyroute2(Connection()):

        def raise_lookup_device_error(self, tap_dev_name, caused_by=None):
            raise NetworkBackendConnectionError("Device '%s' not found!" % tap_dev_name) from caused_by

        def lookup_device(self, tap_dev_name):
            try:
                idx_tap_x = singletons.network_backend.get_ipdb().interfaces[tap_dev_name]
                return idx_tap_x

            except KeyError as e:
                raise self.raise_lookup_device_error(tap_dev_name) from e

        def _tap_link_up(self, tap_x, tap_y, up=True):

            dev = self.lookup_device(tap_x)

            # get_ipdb_logger().info("%s = get_ipdb_singleton().interfaces['%s']" % (tap_x, tap_x))

            if not singletons.network_backend.connection_book_keeper.interface_states[tap_x]:
                if up:
                    # get_ipdb_logger().info("%s.up()" % dev['ifname'])
                    dev.up()
            else:
                if not up:
                    # get_ipdb_logger().info("%s.down()" % dev['ifname'])
                    dev.down()

            # remember that the device is up (or down)
            singletons.network_backend.connection_book_keeper.interface_states.toggle_state(tap_x, up)

    return ConnectionPyroute2


def ConnectionPyroute2IPRoute():
    class ConnectionPyroute2IPRoute(Connection()):

        def raise_lookup_device_error(self, tap_dev_name, caused_by=None):
            raise NetworkBackendConnectionError("Device '%s' not found!" % tap_dev_name) from caused_by

        def _tap_link_up(self, tap_x, tap_y, up=True):

            if not singletons.network_backend.connection_book_keeper.interface_states[tap_x]:
                if up:
                    singletons.network_backend.p_links_up.add(tap_x)

            else:
                if not up:
                    singletons.network_backend.p_links_down.add(tap_x)

            # remember that the device is up (or down)
            singletons.network_backend.connection_book_keeper.interface_states.toggle_state(tap_x, up)

    return ConnectionPyroute2IPRoute
