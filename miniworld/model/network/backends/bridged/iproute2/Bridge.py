from pprint import pformat
from subprocess import check_output

from ordered_set import OrderedSet

from miniworld.errors import NetworkBackendBridgedBridgeError
from miniworld.model.network.backends.bridged.Bridge import Bridge
from miniworld.model.network.backends.bridged.iproute2 import IPRoute2Commands
from miniworld.model.singletons.Singletons import singletons

# TODO: use group mgmt functions!


def BridgeIproute2():
    # TODO: extract iproute2 commands!
    class BridgeIproute2(Bridge):

        """
        Attributes
        ----------
        id : str
            Name of the bridge.
        bridge:
        """

        EVENT_ROOT = "bridge"
        EVENT_BRIDGE_ADD = "bridge_add"

        _BRIDGE_PAR = "bridge_parallel"
        EVENT_BRIDGE_UP = _BRIDGE_PAR  # "bridge_up"
        EVENT_BRIDGE_ADD_IF = _BRIDGE_PAR  # "bridge_add_if"
        EVENT_BRIDGE_SET_HUB = _BRIDGE_PAR  # "bridge_set_hub"
        EVENT_BRIDGE_UP_IF = _BRIDGE_PAR  # "bridge_up_if"
        EVENT_BRIDGE_SET_GROUP_IF = _BRIDGE_PAR
        EVENT_ORDER = OrderedSet([EVENT_BRIDGE_ADD, _BRIDGE_PAR])  # EVENT_BRIDGE_SET_HUB, EVENT_BRIDGE_UP, EVENT_BRIDGE_ADD_IF, EVENT_BRIDGE_UP_IF])

        # TODO: var for prefixes
        def add_shell_command(self, event, cmd):
            singletons.network_backend.shell_command_executor.add_command(self.EVENT_ROOT, event, self.id, cmd, ["bridge"])

        def _start(self, bridge_dev_name=None, switch=False):
            """
            Create the bridge, add it to the bridge group and set the hub mode if appropriate.

            Parameters
            ----------
            bridge_dev_name
            switch

            Returns
            -------

            """

            self.bridge_dev_name = bridge_dev_name
            br_add_cmd = self._get_bridge_add_cmd()
            # br_set_group_cmd = IPRoute2Commands.get_add_interface_to_group_cmd(self.bridge_dev_name, IPRoute2Commands.GROUP_BRIDGES)

            self.add_shell_command(self.EVENT_BRIDGE_ADD, br_add_cmd)
            # self.add_shell_command(self.EVENT_BRIDGE_SET_GROUP_IF, br_set_group_cmd)

            if not switch:
                br_set_hub_cmd = self._get_bridge_set_hub_mode_cmd()
                self.add_shell_command(self.EVENT_BRIDGE_SET_HUB, br_set_hub_cmd)

        def add_if(self, _if_name, if_up=True):

            try:

                br_add_if_cmd = self._get_bridge_add_if_cmd(_if_name=_if_name)
                self.add_shell_command(self.EVENT_BRIDGE_ADD_IF, br_add_if_cmd)

                self.add_shell_command(self.EVENT_BRIDGE_UP_IF, self._get_bridge_up_cmd(_if_name))
                self.add_shell_command(self.EVENT_BRIDGE_UP, self._get_bridge_up_cmd(self.bridge_dev_name))

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

        def _get_bridge_add_cmd(self):
            return IPRoute2Commands.get_bridge_add_cmd(self.bridge_dev_name)

        def _get_bridge_set_hub_mode_cmd(self):
            return IPRoute2Commands.get_bridge_set_hub_mode_cmd(self.bridge_dev_name)

        def _get_bridge_add_if_cmd(self, _if_name):
            return IPRoute2Commands.get_bridge_add_if_cmd(_if_name, self.bridge_dev_name)

        def _get_bridge_up_cmd(self, _if_name):
            return IPRoute2Commands.get_interface_up_cmd(_if_name)

    return BridgeIproute2
