from miniworld import singletons
from miniworld.model.network.backends.bridged.Connection import ConnectionDummy
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import *

def ConnectionMultiBridges():
    class ConnectionMultiBridges(ConnectionDummy()):

        #########################################
        ### Superclass stuff
        #########################################

        # TODO: #84 move to NetworkBackendBridgedMultiDevice
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

        # def shape_device(self, dev_name, connection_id, link_quality_dict):
        #     '''
        #     Parameters
        #     ----------
        #     dev_name : str
        #     connection_id : str
        #     rate : int
        #
        #     tc qdisc add dev $DEV root handle 1:0 htb default 12
        #     tc class add dev $DEV parent 1:0 classid 1:1 htb rate 190kbit ceil 190kbit
        #     tc class add dev $DEV parent 1:1 classid 1:12 htb rate 100kbit ceil 190kbit prio 2
        #     '''
        #
        #     rate = link_quality_dict.get(LINK_QUALITY_KEY_BANDWIDTH)
        #     delay = link_quality_dict.get(LINK_QUALITY_KEY_DELAY)
        #
        #     if rate is not None:
        #
        #         # if singletons.simulation_manager.current_step == 0:
        #         # add root
        #         self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_QDISC,
        #                                # TODO: ADD/REMOVE default 1
        #                                "tc qdisc replace dev {} root handle 1:0 htb default 1".format(dev_name))
        #
        #         # add first and only class, use htb shaping algorithm
        #         self.add_shell_command(self.EVENT_LINK_SHAPE_ADD_CLASS,
        #                                "tc class replace dev {} parent 1:0 classid 1:{id} htb rate {rate}kbit".format(
        #                                    dev_name, rate=rate, id=connection_id))

    return ConnectionMultiBridges