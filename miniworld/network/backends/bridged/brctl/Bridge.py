from miniworld.network.backends.bridged.iproute2.Bridge import BridgeIproute2


def BridgeBrctl():
    class BridgeBrctl(BridgeIproute2()):

        """
        Attributes
        ----------
        id : str
            Name of the bridge.
        bridge:
        """

        def _get_bridge_add_cmd(self):
            return "brctl addbr {}".format(self.bridge_dev_name)

        def _get_bridge_set_hub_mode_cmd(self):
            return "brctl setageing {} 0".format(self.bridge_dev_name)

        def _get_bridge_add_if_cmd(self, _if_name):
            return "brctl addif {bridge} {_if}".format(_if=_if_name, bridge=self.bridge_dev_name)

    return BridgeBrctl
