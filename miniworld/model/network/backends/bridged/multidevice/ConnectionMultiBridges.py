from miniworld import singletons
from miniworld.model.network.backends.bridged.Connection import ConnectionDummy


def ConnectionMultiBridges():
    class ConnectionMultiBridges(ConnectionDummy()):

        #########################################
        # Superclass stuff
        #########################################

        def tap_link_up(self, tap_x, tap_y, up=True):

            # use internal :py:class:`.connection_book_keeper` to only change the NIC state if necessary
            state_correct = up and singletons.network_backend.connection_book_keeper.interface_states[tap_x]

            if not state_correct:
                self._tap_link_up(tap_x, tap_y, up=up)

        def tap_link_up_central(self, tap_x, tap_y, up=True):

            self.tap_link_up(tap_x, tap_y, up=up)

        @staticmethod
        def get_connection_id(tap_x, tap_y):
            return 1

        def _add_filter_cmd(self, dev_name, connection_id):
            pass

        def _get_default_class(self):
            return 1

    return ConnectionMultiBridges
