import enum

from typing import Dict

from miniworld import singletons
from miniworld.impairment import LinkQualityConstants
from miniworld.misc.InterfaceDependentID import InterfaceDependentID
from miniworld.model import StartableObject


class AbstractConnection(StartableObject.ScenarioState, InterfaceDependentID):
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

    # TODO: use for node, connection and interface
    class ConnectionType(enum.Enum):
        user = 'user'
        mgmt = 'mgmt'
        central = 'central'

    # TODO: add step_added
    def __init__(self, emulation_node_x, emulation_node_y, interface_x, interface_y,
                 connection_type: ConnectionType = ConnectionType.user, is_remote_conn: bool = None,
                 impairment: Dict = None, connected: bool = None,
                 _id: int = None, step_added: int = None
                 ):
        StartableObject.ScenarioState.__init__(self)
        self._id = _id
        self.emulation_node_x = emulation_node_x
        self.emulation_node_y = emulation_node_y
        self.interface_x = interface_x
        self.interface_y = interface_y
        self.connection_type = connection_type
        self.is_remote_conn = is_remote_conn
        self.impairment = impairment
        self.connected = connected
        self.step_added = step_added

        self.emulation_node_x_idid = self.get_interface_class_dependent_id(emulation_node_x._id,
                                                                           self.interface_x.node_class,
                                                                           self.interface_x.nr_host_interface)
        self.emulation_node_y_idid = self.get_interface_class_dependent_id(emulation_node_y._id,
                                                                           self.interface_y.node_class,
                                                                           self.interface_y.nr_host_interface)

        # TODO: REMOVE/RENAME? ?
        self.id = '%s,%s' % (self.emulation_node_x_idid, self.emulation_node_y_idid)

        # create extra node logger
        self.nlog = singletons.logger_factory.get_node_logger(self.id)

    @classmethod
    def from_connection_info(cls, emulation_node_x, emulation_node_y, interface_x, interface_y,
                             connection_info: 'ConnectionInfo'):
        return cls(emulation_node_x=emulation_node_x, emulation_node_y=emulation_node_y,
                   interface_x=interface_x, interface_y=interface_y,
                   connection_type=connection_info.connection_type,
                   is_remote_conn=connection_info.is_remote_conn,
                   step_added=connection_info.step_added,
                   )

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
        bandwidth = link_quality_dict.get(LinkQualityConstants.LINK_QUALITY_KEY_BANDWIDTH)
        loss = link_quality_dict.get(LinkQualityConstants.LINK_QUALITY_KEY_LOSS)

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
        return singletons.simulation_manager.get_central_node(self.emulation_node_x, self.emulation_node_y,
                                                              self.interface_x, self.interface_y)

    # TODO: set correct doc ref
    def get_remote_node(self):
        """
        See :py:meth:`.SimulationManager`
        """
        return singletons.simulation_manager.get_remote_node(self.emulation_node_x, self.emulation_node_y,
                                                             self.interface_x, self.interface_y)
