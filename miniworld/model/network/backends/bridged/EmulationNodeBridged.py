from miniworld.model.singletons.Singletons import singletons
from miniworld.model.emulation.nodes import EmulationNode


class EmulationNodeBridged(EmulationNode.EmulationNode):

    def do_network_config_after_pre_shell_commands(self):
        super(EmulationNodeBridged, self).do_network_config_after_pre_shell_commands()

        # TODO:
        # set NIC state up
        for _if in self.network_mixin.interfaces:
            tap = singletons.network_backend.get_tap_name(self.id, _if)
            # TODO: abstract NIC COMMANDS!
            cmd = "ifconfig {} up" .format(tap)
            singletons.shell_helper.run_shell("host shell", cmd, prefixes=[str(self.id)])
