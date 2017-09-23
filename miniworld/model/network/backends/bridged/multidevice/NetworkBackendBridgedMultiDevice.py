from miniworld import log
from miniworld.management.network.manager.provisioner.NetworkConfiguratorP2P import NetworkConfiguratorP2P
from miniworld.model.network.backends import InterfaceFilter
from miniworld.model.network.backends.bridged.NetworkBackendBridged import NetworkBackendBridgedDummy
from miniworld.model.network.connections.Connections import Connections


def NetworkBackendBridgedMultiDevice():

    class NetworkBackendBridgedMultiDevice(NetworkBackendBridgedDummy()):

        def get_interface_filter(self):
            return InterfaceFilter.AllInterfaces

        def get_network_provisioner(self):
            return NetworkConfiguratorP2P

        #############################################################
        # NetworkBackendNotifications
        #############################################################

        def do_network_topology_change(self):
            pass

        # TODO: put in NetworkBackend whether we have a central node or not ...
        def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info,
                                      start_activated=False, **kwargs):
            """
            Check if a connection shall be created between the nodes and the interfaces.
            Create for ach new connection a bridge.
            """

            connection = None
            # let the NetworkBackend decide whether the links really shall be connected

            connected, bridge = self.create_connection(emulation_node_x, emulation_node_y, interface_x, interface_y)

            if connected:
                # create connection
                connection = self.network_backend_bootstrapper.connection_type(emulation_node_x, emulation_node_y, interface_x, interface_y, connection_info)
                # TODO: does nothing atm
                connection.start(self)
                log.debug("created connection between: %s@%s, %s@%s", emulation_node_x, interface_x, emulation_node_y, interface_y)

            return connected, bridge, connection

        #############################################################
        # Bridge/Connection handling
        #############################################################

        # TODO: move connection_book_keeper here ...
        def create_connection(self, emulation_node_x, emulation_node_y, interface_x, interface_y):
            """ Create a connection between the nodes for the given interfaces, but let the backend device whether a connection
            is needed/shall be created.

            Steps:
            1. Get bridge
            2. Get tap name
            3. Add tap to bridge
            4. Remember connection

            Returns
            -------
            bool, Bridge
                First argument described whether a connection has been created and established.
            """
            connected = False
            connections = Connections([(emulation_node_x, interface_x), (emulation_node_y, interface_y)])

            # TODO:
            # check which node/interface we have
            # TODO: put in NetworkBackend whether we have a central node or not ...
            is_hubwifi = bool(connections.filter_central_nodes())
            is_mgmt_node = bool(connections.filter_mgmt_nodes())

            is_one_tap_mode = is_hubwifi or is_mgmt_node

            bridge = None

            # we have only one tap here
            if is_one_tap_mode:

                virtual_node, _if = None, None
                if is_hubwifi:
                    virtual_node, _if = connections.filter_central_nodes()[0]
                elif is_mgmt_node:
                    virtual_node, _if = connections.filter_mgmt_nodes()[0]

                emu_node, emu_if = connections.filter_real_emulation_nodes()[0]
                tap_dev_name = self.get_tap_name(emu_node.id, emu_if)
                bridge = virtual_node.switch
                bridge.add_if(tap_dev_name, if_up=True)

                self.connection_book_keeper.remember_unidirectional_connection(tap_dev_name)

                connected = True

            # we have 2 taps here: 2 tap devices connected with one L2 bridge
            else:
                create_new_conn = self.connection_book_keeper.should_create_new_connection(
                    emulation_node_x, emulation_node_y, interface_x, interface_y)

                if create_new_conn:
                    # get tap device name
                    tap_x = self.get_tap_name(emulation_node_x.id, interface_x)
                    tap_y = self.get_tap_name(emulation_node_y.id, interface_y)

                    # create bridge
                    bridge = self.create_n_store_switch(emulation_node_x,
                                                        emulation_node_y,
                                                        interface_x)
                    # add devices to bridge
                    bridge.add_if(tap_x, if_up=True)
                    bridge.add_if(tap_y, if_up=True)

                    self.connection_book_keeper.remember_bidirectional_connection(
                        emulation_node_x, emulation_node_y, interface_x, interface_y)

                    connected = True

            return connected, bridge

    return NetworkBackendBridgedMultiDevice
