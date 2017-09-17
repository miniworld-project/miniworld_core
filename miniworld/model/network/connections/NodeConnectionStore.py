from miniworld.model.collections.TupleUserDict import TupleUserDict
from miniworld.model.emulation.nodes.EmulationNode import EmulationNode
from miniworld.model.emulation.nodes.EmulationNodes import EmulationNodes
from miniworld.model.network.connections.JSONEncoder import ConnectionEncoder, JSONStrMixin


class NodeConnectionStore(JSONStrMixin, TupleUserDict):
    """
    Default value for non-existent keys is: NICConnectionStore.

    Attributes
    ----------
    data : dict<(EmulationNodes, NICConnectionStore>

    Examples
    --------
    >>> emu_node1, emu_node2 = ...
    >>> ci = NodeConnectionStore()
    >>> # Get connection information between the two hosts
    >>> ci[(emu_node1, emu_node2)]
    """

    #########################################
    # Magic Methods
    #########################################

    def __init__(self, data=None):
        self.data = data if data is not None else {}

    #########################################
    # MyUserDict
    #########################################

    # TODO: implement same behaviour via magic methods ...
    @staticmethod
    def _get_key(emu_node_x, emu_node_y):
        """
        Get the key to access the dict via slicing.

        Assume we have bidirectional links.
        Therefore, we have the same connection between
        emu_node_x and  emu_node_y as well as
        emu_node_y and emu_node_x.

        Parameters
        ----------
        emu_node_x : EmulationNode
        emu_node_y : EmulationNode

        Returns
        -------
        EmulationNodes
        """
        return EmulationNodes((emu_node_x, emu_node_y)).sorted()


if __name__ == '__main__':
    import json
    from miniworld import testing
    testing.init_testing_environment()

    print(list(testing.get_pairwise_connected_nodes(3)))
    (n1, i1, conn), (n2, i2, _), _ = list(testing.get_pairwise_connected_nodes(2))
    ncs = NodeConnectionStore()
    ncs[EmulationNodes((n1, n2))]
    print(ncs)
    print((n1, n2) in ncs)

    print(json.dumps(ncs, cls=ConnectionEncoder))
