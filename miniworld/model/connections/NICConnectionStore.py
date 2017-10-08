from miniworld.model.TupleUserDict import TupleUserDict
from miniworld.model.connections.JSONEncoder import JSONStrMixin


class NICConnectionStore(TupleUserDict, JSONStrMixin):
    """
    Models the connections between two interfaces.
    Default value is: dict

    Attributes
    ----------
    data : dict<(Interfaces, ConnectionDetails)
    """

    #########################################
    # Magic Methods
    #########################################

    def __init__(self, data=None):
        self.data = data if data is not None else {}

    #########################################
    # TupleUserDict
    #########################################

    # TODO: implement same behaviour via magic methods ...
    @staticmethod
    def _get_key(interface_x, interface_y):
        """

        Parameters
        ----------
        interface_x : Interface
        interface_y: Interface

        Returns
        -------
        Interfaces
        """
        import miniworld.model.interface.Interfaces
        # order on EmulationNode is sufficient for tuple sort
        return miniworld.model.interface.Interfaces.Interfaces([interface_x, interface_y])
