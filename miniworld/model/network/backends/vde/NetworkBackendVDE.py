
from miniworld import log
from miniworld.management.network.manager.provisioner.NetworkConfiguratorSameSubnet import NetworkConfiguratorSameSubnet
from miniworld.model.emulation.nodes.virtual.CentralNode import is_central_node_interface
from miniworld.model.network.backends import NetworkBackends
from miniworld.model.network.backends import InterfaceFilter
from miniworld.model.network.backends.NetworkBackend import NetworkBackendDummy
from miniworld.model.network.backends.vde import Wirefilter
from miniworld.model.network.interface.Interface import HubWiFi

__author__ = 'Nils Schmidt'


class NetworkBackendVDE(NetworkBackendDummy):

    '''
    Attributes
    ----------
    switches: dict<Interface, AbstractSwitch>
        One AbstractSwitch for each interface.
    '''

    def __init__(self, *args, **kwargs):
        super(NetworkBackendVDE, self).__init__(*args, **kwargs)
        self.switches = {}

    def get_interface_filter(self):
        return InterfaceFilter.EqualInterfaceNumbers

    def get_network_provisioner(self):
        return NetworkConfiguratorSameSubnet

    def _start(self, *args, **kwargs):
        pass

    def before_link_initial_start(self, network_backend, emulation_node_x, emulation_node_y, interface_x, interface_y,
                                  connection_info, start_activated=False, **kwargs):

        connection = Wirefilter.Wirefilter(emulation_node_x, emulation_node_y, interface_x, interface_y)
        connection.start(start_activated=start_activated)

        vde_switch_x = emulation_node_x.network_mixin.switches[interface_x]
        vde_switch_y = emulation_node_y.network_mixin.switches[interface_y]
        return True, (vde_switch_x, vde_switch_y), connection

    def before_link_quality_adjustment(self, connection, link_quality_still_connected, link_quality_dict,
                                       network_backend, emulation_node_x, emulation_node_y, interface_x,
                                       interface_y, connection_info,
                                       **kwargs):
        '''
        Adjust the link quality.
        '''
        connection.adjust_link_quality(link_quality_dict)

    def get_interface_index(self, emulation_node, interface):
        return emulation_node.network_mixin.interfaces.index(interface)

    def create_n_connect_central_nodes(self, interfaces):
        '''

        Parameters
        ----------
        interfaces

        Returns
        -------
        dict<int, CentralNode>
        '''
        # create CentralNode s but only if there is a HubWiFi interface
        # TODO: REMOVE
        cnt = 0
        central_nodes_dict = {}
        for _if in filter(lambda x: is_central_node_interface(x), interfaces):
            if cnt == 1:
                raise ValueError("Only one '%s' interface support at the moment!" % HubWiFi)

            # TODO: REFACTOR!
            # TODO: #54: make amount of nodes configurable
            count_central_nodes = 1  # multiprocessing.cpu_count()
            network_backend_bootstrapper = NetworkBackends.get_current_network_backend_bootstrapper()
            for _ in range(0, count_central_nodes):
                # create an own network backend for each node
                #new_emulation_node_network_backend = network_backend_bootstrapper.emulation_node_network_backend_type(network_backend_bootstrapper)

                central_node = network_backend_bootstrapper.central_node_type(network_backend_bootstrapper)
                # TODO: #54 make configurable!
                log.debug("creating CentralNode with id: %s", central_node.id)
                central_node.start(switch=False)
                central_nodes_dict[central_node.id] = central_node

                # create a reference so that the :py:class:`.AbstractConnection` can access it
                # to make a connection
                self.switches[_if] = central_node.switch
            # connect CentralHub s pairwise to each other
            central_nodes = central_nodes_dict.values()
            log.info("connecting CentralHubs pairwise to each other ...")
            # for i1 in range(0, count_central_nodes):
            #     for i2 in range(0, count_central_nodes):
            #         if i1 != i2:
            for i1, i2 in zip(range(0, count_central_nodes), range(1, count_central_nodes)):
                node_x, node_y = central_nodes[i1], central_nodes[i2]
                node_x.connect_to_emu_node(self, node_y)

            cnt += 1

        return central_nodes_dict
