
class InterfaceFilter:

    def __init__(self, *args, **kwargs):
        pass

    def get_interfaces(self, emulation_node_x, emulation_node_y):
        """

        Attributes
        ----------
        emulation_node_x: EmulationNode
        emulation_node_y: EmulationNode

        Returns
        -------
        generator<(Interface, Interface)>
        """
        pass


class EqualInterfaceNumbers(InterfaceFilter):
    """
    Assumes each node has the same number of interfaces.
    And that the interfaces are sorted!

    """

    def __init__(self, *args, **kwargs):
        self.cnt_interfaces = None

    def get_interfaces(self, emulation_node_x, emulation_node_y):
        self.cnt_interfaces = len(emulation_node_x.network_mixin.interfaces.filter_normal_interfaces())

        interfaces_x = emulation_node_x.network_mixin.interfaces.filter_normal_interfaces()
        interfaces_y = emulation_node_y.network_mixin.interfaces.filter_normal_interfaces()

        for i in range(self.cnt_interfaces):
            yield interfaces_x[i], interfaces_y[i]


class CoreInterfaces(InterfaceFilter):
    pass


class AllInterfaces(InterfaceFilter):

    def get_interfaces(self, emulation_node_x, emulation_node_y):

        # TODO: speed improvement by not calling the filter every time?
        for interface_x in emulation_node_x.network_mixin.interfaces.filter_normal_interfaces():
            for interface_y in emulation_node_y.network_mixin.interfaces.filter_normal_interfaces():
                yield interface_x, interface_y
