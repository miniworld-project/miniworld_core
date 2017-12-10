from miniworld.model.domain.connection import Connection


class NetworkBackendBootStrapper:
    """
    Bundles the components a :py:class:`.NetworkBackend` needs to operate.

    Attributes
    ----------
    network_backend_type : type
    emulation_node_type : type
    virtualization_layer_type : type
    connection_type : type
    switch_type : type
    network_configurator_type : type
    central_node_type : type
        Only use the central mode if the backend provides a class for it.
    management_node_type : type
        Only use the management mode if the backend provides a class for it.
    virtual_node_network_backend_type : type
    tunnel_type : type
    """

    def __init__(self,
                 network_backend_type,
                 emulation_node_type,
                 virtualization_layer_type,
                 connection_service,
                 switch_type,
                 network_configurator_type,
                 central_node_type=None,
                 management_node_type=None,
                 tunnel_type=None,
                 connection_type=None
                 ):

        if connection_type is None:
            connection_type = Connection

        self.network_backend_type = network_backend_type

        # domain models
        self.connection_type = connection_type
        self.switch_type = switch_type
        self.emulation_node_type = emulation_node_type
        self.tunnel_type = tunnel_type

        # domain service (singleton until the scenario changes)
        self.connection_service = connection_service()

        self.network_configurator_type = network_configurator_type
        self.virtualization_layer_type = virtualization_layer_type
        self.central_node_type = central_node_type
        self.management_node_type = management_node_type
