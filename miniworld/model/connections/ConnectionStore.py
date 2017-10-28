from collections import UserDict
from collections import defaultdict

from typing import Tuple, Iterator

from miniworld.errors import Base
from miniworld.model.connections.NodeConnectionStore import NodeConnectionStore
from miniworld.model.connections.ConnectionDetails import ConnectionDetails
from miniworld.model.connections.JSONEncoder import JSONStrMixin
from miniworld.model.connections.NICConnectionStore import NICConnectionStore
from miniworld.model.connections.NodeDictMixin import NodeDict
from miniworld.model.interface.Interfaces import Interfaces
from miniworld.network.AbstractConnection import AbstractConnection
from miniworld.nodes.EmulationNodes import EmulationNodes


class UnknownConnection(Base):
    pass


class ConnectionStore(UserDict, JSONStrMixin):
    KEY_CONN_ACTIVE = 'active'
    KEY_CONN_NOT_ACTIVE = 'not_active'

    """
    Manages the network connections between :py:class:`.EmulationNode`s.
    The connections are separated into `active` and `inactive` connections.

    Attributes
    ----------
    data : dict<str, NodeConnectionStore>
        Stores the connections.

    Examples
    --------
    >>> from miniworld import testing
    >>> testing.init_testing_environment()
    >>> conn_store = list(testing.get_pairwise_connected_nodes(2))[-1]

    >>> # Pretty printing
    >>> print str(conn_store.get_active_node_connection_store())
    {('1', '2'): {"('mesh', 'mesh')": {'loss': 0.5, 'bandwidth': 500}}, ('2', '3'): {"('mesh', 'mesh')": {'loss': 0.5, 'bandwidth': 500}}}

    >>> print conn_store.get_link_quality_matrix(include_interfaces=False, key=LINK_QUALITY_KEY_LOSS)
    {('1', '2'): 0.5, ('2', '3'): 0.5}

    >>> # JSON export
    >>> print conn_store.get_link_quality_matrix(include_interfaces=False, key=LINK_QUALITY_KEY_LOSS).to_json()
    {
        "('1', '2')": 0.5,
        "('2', '3')": 0.5
    }
    >>> print conn_store.get_link_quality_matrix(include_interfaces=False).to_json()
    {
        "('1', '2')": {
            "loss": 0.5,
            "bandwidth": 500
        },
        "('2', '3')": {
            "loss": 0.5,
            "bandwidth": 500
        }
    }
    >>> print conn_store.get_link_quality_matrix(include_interfaces=True).to_json()
    {
        "('1', '2')": [
            [
                "mesh",
                "mesh"
            ],
            {
                "loss": 0.5,
                "bandwidth": 500
            }
        ],
        "('2', '3')": [
            [
                "mesh",
                "mesh"
            ],
            {
                "loss": 0.5,
                "bandwidth": 500
            }
        ]
    }

    >>> print conn_store.get_link_quality_matrix(include_interfaces=True, key=LINK_QUALITY_KEY_LOSS).to_json()
    {
        "('1', '2')": [
            [
                "mesh",
                "mesh"
            ],
            {
                "loss": 0.5
            }
        ],
        "('2', '3')": [
            [
                "mesh",
                "mesh"
            ],
            {
                "loss": 0.5
            }
        ]
    }

    >>> print conn_store.get_connections_per_node().to_json()
    {
        "1": [
            2,
            3,
            5,
            4
        ],
        "3": [
            4
        ],
        "2": [
            5,
            3
        ],
        "4": [
            5
        ]
    }
    """

    def __init__(self, data=None):
        """

        Parameters
        ----------
        data: optional (default is `dict<str, NodeConnectionStore>`)

        """
        if data is None:
            self.data = {}
            self[self.KEY_CONN_ACTIVE] = NodeConnectionStore()
            self[self.KEY_CONN_NOT_ACTIVE] = NodeConnectionStore()
        else:
            self.data = data

    #########################################
    # Iterators
    #########################################

    def iter_connections(self):
        """

        Generator
        ---------
        EmulationNodes, Interfaces
        """
        node_connection_store = self.get_active_node_connection_store()
        for emu_nodes, nic_connections in node_connection_store.items():

            for ifaces in nic_connections.keys():
                yield emu_nodes, ifaces

    def get_active_interfaces_per_connection(self):
        """
        Examples
        --------

        Returns
        -------
        dict<EmulationNodes, tuple<Interfaces>>
        """
        active_connections = self.get_active_node_connection_store()

        res = {}
        for key, vals in active_connections.items():
            # may be empty dict
            if vals:
                res[key] = tuple(vals.keys())
        return res

    def get_connections_per_node(self, active=True):
        """

        Returns
        -------
        dict<EmulationNode, set<EmulationNode>>
        """
        network_topo = defaultdict(set)
        for emulation_node_x, emulation_node_y in self.get_connections_explicit(active=active).keys():
            network_topo[emulation_node_x].add(emulation_node_y)
        return network_topo

    #########################################
    # Connection Management
    #########################################

    # TODO: #54,#55
    def add_connection(self, connection: AbstractConnection,
                       active=True, link_quality_dict=None):
        """

        Parameters
        ----------
        emu_node_x : EmulationNode
        emu_node_y : EmulationNode
        interface_x : Interface
        interface_y: Interface
        connection : AbstractConnection
        active: optional (default is True)
            Add the connection to the active connections.
        link_quality_dict: optional (default is None)
            May not be present at this time.
        """
        emu_node_x = connection.emulation_node_x
        emu_node_y = connection.emulation_node_y
        interface_x = connection.interface_x
        interface_y = connection.interface_y

        conns = self.get_connections_explicit(active).get((emu_node_x, emu_node_y))
        if not conns:
            # create new NICConnectionStore
            conns = self.get_connections_explicit(active)[(emu_node_x, emu_node_y)] = NICConnectionStore()

        key = interface_x, interface_y
        conns[key] = ConnectionDetails(connection, link_quality_dict)

    def get_active_node_connection_store(self):
        """
        Returns
        -------
        NodeConnectionStore
        """
        return self[self.KEY_CONN_ACTIVE]

    def get_inactive_node_connection_store(self):
        """
        Returns
        -------
        NodeConnectionStore
        """
        return self[self.KEY_CONN_NOT_ACTIVE]

    def get_connections_explicit(self, active=True):
        """
        Get a connection.

        Parameters
        ----------
        active: bool, optional (defualt is True)
            Search for the connection in the `active` connections.
            Otherwise in the inactive ones.

        Returns
        -------
        ConnectionInfos
        """
        if active:
            return self.get_active_node_connection_store()
        else:
            return self.get_inactive_node_connection_store()

    def get_connections_for_nodes_implicit(self, emu_node_x, emu_node_y, interface_x, interface_y):
        """
        Get the connection implicit from the `active` or `inactive` connections.
        NOTE: there is exactly one connection!

        Parameters
        ----------
        emu_node_x: EmulationNode
        emu_node_y: EmulationNode
        interface_x : Interface
        interface_y : Interface

        Returns
        -------
        str, NICConnectionStore
            The dict key, the connections dict.
        None, None
        """
        key = emu_node_x, emu_node_y
        nic_connection_store = self.get_active_node_connection_store().get(key)
        if nic_connection_store and (interface_x, interface_y) in nic_connection_store:
            return self.KEY_CONN_ACTIVE, nic_connection_store
        else:
            nic_connection_store = self.get_inactive_node_connection_store().get(key)
            if nic_connection_store and (interface_x, interface_y) in nic_connection_store:
                return self.KEY_CONN_NOT_ACTIVE, self.get_inactive_node_connection_store().get(key)

        return None, None

    def change_connection_state(self, emu_node_x, emu_node_y, interface_x, interface_y, now_active=True):
        """
        Change the connection state. Therefore, move (if state changed) e.g. from active to inactive connection.

        Parameters
        ----------
        emu_node_x : EmulationNode
        emu_node_y : EmulationNode
        interface_x : Interface
        interface_y : Interface
        now_active : bool
            Whether the connection is still `active`.

        Returns
        -------
        bool
            If the state changed

        Raises
        ------
        UnknownConnection
            If the connection is unknown
        """
        node_key = emu_node_x, emu_node_y
        iface_key = interface_x, interface_y
        key = node_key + iface_key
        was_active_str, nic_connection_store = self.get_connections_for_nodes_implicit(*key)
        was_active = was_active_str == self.KEY_CONN_ACTIVE

        # there is only one element for this particular key
        connection_details = list(nic_connection_store.items())[0][1]

        if not nic_connection_store:
            raise UnknownConnection(
                "There is no connection between %s@%s <->%s@%s" % (emu_node_x, emu_node_y, interface_x, interface_y))

        # connection change
        if was_active != now_active:

            # change: inactive -> active
            if not was_active and now_active:
                try:
                    # delete from the inactive connections
                    del self[self.KEY_CONN_NOT_ACTIVE][node_key][iface_key]
                    # delete dict for nodes if no active iface any more
                    if len(self[self.KEY_CONN_NOT_ACTIVE][node_key]) == 0:
                        del self[self.KEY_CONN_NOT_ACTIVE][node_key]
                    # move to active connections
                    self[self.KEY_CONN_ACTIVE][node_key][iface_key] = connection_details

                except KeyError:
                    pass
            # change: active -> inactive
            elif was_active and not now_active:
                try:
                    # delete from the active connections
                    del self[self.KEY_CONN_ACTIVE][node_key][iface_key]
                    # delete dict for nodes if no active iface any more
                    if len(self[self.KEY_CONN_ACTIVE][node_key]) == 0:
                        del self[self.KEY_CONN_ACTIVE][node_key]
                    # move to inactive connections
                    self[self.KEY_CONN_NOT_ACTIVE][node_key][iface_key] = connection_details
                except KeyError:
                    pass
            return True

        return False

    #########################################
    # Link Quality
    #########################################

    def get_link_quality_matrix(self, include_interfaces=True, key=None):
        """

        Parameters
        ----------
        include_interfaces : bool, optional (default is True)
        key : str, optional (default is None)
            If true, project the link quality dict for the `key`

        Returns
        -------
        NodeDict<EmulationNodes, dict<str, object>>
            If `include_interfaces`
        NodeDict<EmulationNodes, object>
            If `include_interfaces` and `key`.

        NodeDict<EmulationNodes, (Interfaces, dict<str, object>)>
            If not `include_interfaces`
                NodeDict<EmulationNodes, object>
        NodeDict<EmulationNodes, (Interfaces, object)>
            If `include_interfaces` and `key`.
        """

        def get_key(emu_nodes, ifaces):
            return emu_nodes

        def get_val(emu_nodes, ifaces):
            connection_details = self.get_link_quality(emu_nodes[0], emu_nodes[1], ifaces[0], ifaces[1])
            res = link_quality_dict = connection_details.link_quality

            if key:
                res = link_quality_dict[key]
            if include_interfaces:
                res = ifaces, link_quality_dict
            return res

        return NodeDict(
            {get_key(emu_nodes, ifaces): get_val(emu_nodes, ifaces) for emu_nodes, ifaces in self.iter_connections()})

    def get_connections(self, emu_node_x, active=True) -> Iterator[Tuple[EmulationNodes, Interfaces, ConnectionDetails]]:
        node_connection_store = self.get_connections_explicit(active=active)
        for emu_nodes, nic_connections in node_connection_store.items():
            if emu_node_x in emu_nodes:
                for ifaces, connection_details in nic_connections.items():
                    yield emu_nodes, ifaces, connection_details

    def get_link_quality(self, emu_node_x, emu_node_y, interface_x, interface_y):
        """

        Parameters
        ----------
        emu_node_x
        emu_node_y
        interface_x
        interface_y

        Returns
        -------
        bool, dict
        """
        key = emu_node_x, emu_node_y, interface_x, interface_y
        interface_key = interface_x, interface_y
        return self.get_connections_for_nodes_implicit(*key)[1][interface_key]

    def update_link_quality(self, emu_node_x, emu_node_y, interface_x, interface_y, connection, connected,
                            link_quality_dict):
        """
        Moves (if connection change) the connection from active to inactive connections depending on `connected`
        Afterwards the link quality gets updated.

        Parameters
        ----------
        emu_node_x
        emu_node_y
        interface_x
        interface_y
        connected
        link_quality_dict

        Returns
        -------
        str
            Active, inactive connection?

        Raises
        ------
        UnknownConnection
        """
        # get connections for nodes
        key = emu_node_x, emu_node_y, interface_x, interface_y
        dict_key, conns = self.get_connections_for_nodes_implicit(*key)
        if not issubclass(conns.__class__, NICConnectionStore):
            raise UnknownConnection("No connection exists for %s,%s.\nConnections: %s" % (emu_node_x, emu_node_y, self))

        # update link quality
        iface_key = interface_x, interface_y

        conns[iface_key].update_link_quality(link_quality_dict)

        return dict_key


if __name__ == "__main__":
    import doctest

    doctest.testmod()
