from miniworld import singletons
from miniworld.log import get_node_logger
from miniworld.model import StartableObject
from miniworld.model.emulation.InterfaceDependentID import InterfaceDependentID
from miniworld.model.network.linkqualitymodels.LinkQualityConstants import LINK_QUALITY_KEY_BANDWIDTH, \
    LINK_QUALITY_KEY_LOSS


class AbstractConnection(StartableObject.StartableSimulationStateObject, InterfaceDependentID):
    """
    Attributes
    ----------
    id : str
    nlog
        Extra node logger.
    emulation_node_x : EmulationNode
    emulation_node_y: EmulationNode
    interface_x : Interface
    interface_y : Interface
    connection_info : ConnectionInfo, optional (default is None)
    """

    def __init__(self, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info=None):
        StartableObject.StartableSimulationStateObject.__init__(self)
        self.emulation_node_x = emulation_node_x
        self.emulation_node_y = emulation_node_y
        self.interface_x = interface_x
        self.interface_y = interface_y

        self.connection_info = connection_info

        self.emulation_node_x_idid = self.get_interface_class_dependent_id(emulation_node_x.id, self.interface_x.node_class, self.interface_x.nr_host_interface)
        self.emulation_node_y_idid = self.get_interface_class_dependent_id(emulation_node_y.id, self.interface_y.node_class, self.interface_y.nr_host_interface)

        self.id = '%s,%s' % (self.emulation_node_x_idid, self.emulation_node_y_idid)

        # create extra node logger
        self.nlog = get_node_logger(self.id)

    # TODO: adjust doc: set the link up ...
    def start(self, start_activated=False):
        """
        Start the connection.

        Parameters
        ----------
        start_activated  : bool, optional (default is False)
            Start the connection in active mode, letting all packets pass through.
        """
        raise NotImplementedError

    def adjust_link_quality(self, link_quality_dict):
        """

        Parameters
        ----------
        link_quality_dict

        Returns
        -------
        """
        # assumes only equal interfaces can be connected to each other
        bandwidth = link_quality_dict.get(LINK_QUALITY_KEY_BANDWIDTH)
        loss = link_quality_dict.get(LINK_QUALITY_KEY_LOSS)

        if bandwidth is not None:
            pass
        if loss is not None:
            pass
        raise NotImplementedError

    #####################################
    # Convenient methods
    #####################################

    def get_central_node(self):
        """
        See :py:meth:`.SimulationManager`
        """
        return singletons.simulation_manager.get_central_node(self.emulation_node_x, self.emulation_node_y, self.interface_x, self.interface_y)

    # TODO: set correct doc ref
    def get_remote_node(self):
        """
        See :py:meth:`.SimulationManager`
        """
        return singletons.simulation_manager.get_remote_node(self.emulation_node_x, self.emulation_node_y, self.interface_x, self.interface_y)
