from subprocess import CalledProcessError

from miniworld.nodes import EmulationService
from miniworld.singletons import singletons


class EmulationNodeBridged(EmulationService.EmulationService):

    def do_network_config_after_pre_shell_commands(self):
        super(EmulationNodeBridged, self).do_network_config_after_pre_shell_commands()

        # TODO:
        # set NIC state up
        for _if in self._node.interfaces:
            tap = singletons.network_backend.get_tap_name(self._node._id, _if)
            # TODO: abstract NIC COMMANDS!
            cmd = "ifconfig {} up" .format(tap)
            # TODO: REMOVE
            try:
                singletons.shell_helper.run_shell("host shell", cmd, prefixes=[str(self._node._id)])
            except CalledProcessError as e:
                pass
