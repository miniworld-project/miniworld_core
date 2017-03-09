
from miniworld.Config import config
from miniworld.model.network.backends.EmulationNodeNetworkBackend import EmulationNodeNetworkBackend

__author__ = 'Nils Schmidt'

class VirtualNodeNetworkBackend(EmulationNodeNetworkBackend):
    '''

    '''

    def __init__(self, network_backend_bootstrapper, node_id,
                 # network
                 interfaces=None, management_switch=False):

        # skip `EmulationNodeNetworkBackendVDE` in call hieararchy
        super(VirtualNodeNetworkBackend, self).__init__(network_backend_bootstrapper, node_id, interfaces=interfaces,
                                           management_switch=management_switch)
        self.create_switches()

    def _start(self, switch=None, bridge_dev_name=None):
        self.start_switches(switch=switch, bridge_dev_name=bridge_dev_name)
