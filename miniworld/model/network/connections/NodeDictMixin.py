from collections import UserDict

from miniworld.model.network.connections.JSONEncoder import JSONStrMixin


# TODO: REMOVE
class NodeDictMixin:
    '''
    '''

    #########################################
    # Structure Converting
    #########################################

    def to_ids(self):
        '''
        Convert all :py:class:`.EmulationNode` to their id.

        Returns
        -------
        UserDict
            All instances of EmulationNode replaced by their id.

        Examples
        --------
        >>> x = {[EmulationNode(1), EmulationNode(2)]: {'loss': 0.5, 'bandwidth': 500}}
        >>> x.to_ids()
        {('1', '1'): {'loss': 0.5, 'bandwidth': 500}}
        '''
        converted_to_ids = {(emu_node_x.id, emu_node_y.id): val_inner for (emu_node_x, emu_node_y), val_inner in self.items()}
        return self.__class__(converted_to_ids)


class NodeDict(JSONStrMixin, UserDict):
    pass
