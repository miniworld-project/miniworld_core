from miniworld.model.Objects import Objects


class Connections(Objects):

    """
    Attributes
    ----------
    data : list<(EmulationNode, Interface)>
    """

    def filter_central_nodes(self):
        """

        Returns
        -------
        list<(CentralNode, HubWiFi>
        """

        from miniworld.model.emulation.nodes.virtual.CentralNode import is_central_node
        return self.filter_type(fun=lambda x: is_central_node(x[0]))

    def filter_mgmt_nodes(self):
        """

        Returns
        -------
        list<(ManagementNode, Management)>
        """
        from miniworld.model.emulation.nodes.virtual.ManagementNode import is_management_node
        return self.filter_type(fun=lambda x: is_management_node(x[0]))

    def filter_real_emulation_nodes(self):
        """
        Return all nodes which belong to a real emulation (therefore belong to a qemu instance).

        Returns
        -------
        list<EmulationNode>
        """

        from miniworld.model.emulation.nodes.virtual.VirtualNode import VirtualNode
        return self.filter_type(fun=lambda x: not isinstance(x[0], VirtualNode))
