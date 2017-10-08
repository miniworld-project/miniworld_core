from miniworld.network.backends.bridged.Connection import Connection
from miniworld.network.backends.bridged.iproute2 import IPRoute2Commands
from miniworld.singletons import singletons


def ConnectionIproute2():
    class ConnectionIproute2(Connection()):

        def _tap_link_up(self, tap_x, tap_y, up=True):

            cmd = IPRoute2Commands.get_interface_up_cmd(tap_x, state_down=not up)
            self.add_shell_command(self.EVENT_CONN_STATE_CHANGE, cmd)
            # remember that the device is up (or down)
            singletons.network_backend.connection_book_keeper.interface_states.toggle_state(tap_x, up)

    return ConnectionIproute2
