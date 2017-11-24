# TODO: #54: DOC
# TODO: provide context managers!
from miniworld.network.AbstractConnection import AbstractConnection


class NetworkBackendNotifications:
    """ This interface describes the interaction between the :py:class:`.SimulationManager`,
        the :py:class:`.NetworkManager` and the :py:class:`.NetworkBackend`.
    """

    #########################################
    # Per step
    #########################################

    def before_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        """
        Called before the next simulation step is about to be performed.
        Called every step.

        Parameters
        ----------
        simulation_manager : SimulationManager
        step_cnt : int
        network_backend : NetworkBackend
        emulation_nodes : EmulationNodes
        """
        pass

    def after_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
        """
        Called after a simulation step is over.
        Called every step.

        Parameters
        ----------
        simulation_manager
        emulation_nodes
        network_backend
        step_cnt
        """
        pass

    def before_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                       full_distance_matrix, **kwargs):
        """
        Called only if the distance matrix changed.

        Parameters
        ----------
        changed_distance_matrix
        simulation_manager
        network_backend
        full_distance_matrix
        kwargs

        Returns
        -------

        """
        pass

    def after_distance_matrix_changed(self, simulation_manager, network_backend, changed_distance_matrix,
                                      full_distance_matrix, **kwargs):
        """
        Called only if the distance matrix changed.

        Parameters
        ----------
        changed_distance_matrix
        simulation_manager
        network_backend
        full_distance_matrix
        kwargs

        Returns
        -------

        """
        pass

    #########################################
    # Per node
    #########################################

    def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                  start_activated=False, **kwargs):
        """
        Called before a link between the two nodes on the supplied interfaces is going to be created.

        Let the NetworkBackend decide whether the links really shall be connected.
        1) SimulationManager->NetworkManager->NetworkBackend-|
                         SimulationManager<-NetworkManager-| <- connected, connection
           ...
        2) after_link_initial_start() -> ...

        Parameters
        ----------

        network_backend
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y
        connection_info : ConnectionInfo
        start_activated

        Returns
        -------
        Bool, AbstractSwitch, AbstractConnection
            Whether the nodes are connected and the appropriate connection
        """
        pass

    # TODO: REMOVE?
    def after_link_initial_start(self, network_backend_connected, switch, connection, network_backend, emulation_node_x,
                                 emulation_node_y, interface_x, interface_y, connection_info, start_activated=False, **kwargs):
        """

        Parameters
        ----------
        switch
        network_backend_connected : Bool
            Return value from :py:meth:`.before_link_initial_start`
        connection : AbstractConnection
            Return value from :py:meth:`.before_link_initial_start`
        network_backend
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y
        connection_info : ConnectionInfo
        start_activated

        Returns
        -------

        """
        pass

    def before_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                       network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                       connection_info,
                                       **kwargs):
        """
        Called only for connected nodes. There the :py:class:`.LinkQualityModel` and the :py:class:`.NetworkBackend` agreed on a connection.

        Parameters
        ----------
        connection
        link_quality_still_connected
        link_quality_dict
        network_backend
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y
        connection_info : ConnectionInfo
        kwargs
        """
        pass

    def after_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                      network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                      **kwargs):
        """
        Called only for connected nodes. There the :py:class:`.LinkQualityModel` and the :py:class:`.NetworkBackend` agreed on a connection.

        Parameters
        ----------
        connection
        link_quality_still_connected
        link_quality_dict
        network_backend
        emulation_node_x
        emulation_node_y
        interface_x
        interface_y
        connection_info : ConnectionInfo
        kwargs

        Returns
        -------

        """
        pass

    def link_up(self, connection, link_quality_dict,
                network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                **kwargs):
        pass

    def link_down(self, connection, link_quality_dict,
                  network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                  **kwargs):
        pass

        #########################################
        # Distributed Mode
        #########################################

    # TODO: PASS CONNECTION OBJECTS?
    # TODO: return type? Tunnel?
    def connection_across_servers(self, network_backend, emulation_node_x, emulation_node_y, remote_ip):
        """

        Parameters
        ----------
        network_backend
        emulation_node_x
        emulation_node_y
        remote_ip

        Returns
        -------

        """
        pass


class ConnectionInfo:
    __slots__ = (
        'is_remote_conn',
        'connection_type',
    )

    def __init__(self, connection_type: AbstractConnection.ConnectionType = AbstractConnection.ConnectionType.user, is_remote_conn=False):
        self.is_remote_conn = is_remote_conn
        self.connection_type = connection_type

    @property
    def is_one_tap_mode(self) -> bool:
        return self.connection_type in (AbstractConnection.ConnectionType.central, AbstractConnection.ConnectionType.mgmt) or self.is_remote_conn
