from miniworld.service.emulation.interface import InterfaceService


class InterfaceFilter:

    def __init__(self):
        self._interface_service = InterfaceService()

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
        super().__init__()
        self.cnt_interfaces = None

    def get_interfaces(self, emulation_node_x, emulation_node_y):
        self.cnt_interfaces = len(self._interface_service.filter_normal_interfaces(emulation_node_x.interfaces))

        interfaces_x = self._interface_service.filter_normal_interfaces(emulation_node_x.interfaces)
        interfaces_y = self._interface_service.filter_normal_interfaces(emulation_node_y.interfaces)

        for i in range(self.cnt_interfaces):
            yield interfaces_x[i], interfaces_y[i]


class CoreInterfaces(InterfaceFilter):
    pass


class AllInterfaces(InterfaceFilter):

    def get_interfaces(self, emulation_node_x, emulation_node_y):

        # TODO: speed improvement by not calling the filter every time?
        for interface_x in self._interface_service.filter_normal_interfaces(emulation_node_x.interfaces):
            for interface_y in self._interface_service.filter_normal_interfaces(emulation_node_y.interfaces):
                yield interface_x, interface_y
