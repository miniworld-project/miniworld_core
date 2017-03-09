from functools import total_ordering
from threading import Lock

import ipaddress

from miniworld.script.TemplateContentProvider import TemplateContentProvider
from miniworld.util import NetUtil

__author__ = 'Nils Schmidt'

NODE_MAC_PREFIX = "%02x:%06x"

@total_ordering
class Interface(object, TemplateContentProvider):

    node_class = 0
    node_class_name = "abstract"

    '''
    Models an interface class like Access Point or Mesh.

    Attributes
    ----------
    node_class : int
    node_class_name : str
        The name of the node class.
    nr_host_interface: int, optional (default is 1)
        The number of the interface on the host (e.g. eth0 -> 1).
        First number should start with 1!

    Raises
    ------
    ValueError
    '''

    def __init__(self, nr_host_interface = 1):
        object.__init__(self)

        if not nr_host_interface >= 1:
            raise ValueError("The number of the interface has to be greater 0!")

        self.nr_host_interface = nr_host_interface

    def __str__(self):
        return "%s_%d" % (self.node_class_name, self.nr_host_interface)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.nr_host_interface)

    def eq__comp_attrs(self):
        return (self.node_class, self.nr_host_interface)

    def __eq__(self, other):
        if issubclass(other.__class__, Interface):
            return self.eq__comp_attrs() == other.eq__comp_attrs()
        return False

    # greatest is the smallest `node_class` with the smallest `nr_host_interface
    def __lt__(self, other):
        if self.node_class < other.node_class:
            return True
        elif self.node_class == other.node_class:
            return self.nr_host_interface <= other.nr_host_interface

        return False

    def __hash__(self):
        return hash(self.eq__comp_attrs())

    def is_same_interface_type(self, other):
        return self.node_class == other.node_class

    # TODO: get IP from NetworkConfigurator!
    def get_ip(self, node_id):
        '''
        Get the ip for the `node_id.


        Parameters
        ----------
        node_id : int

        Returns
        -------
        ipaddress._BaseAddress
        '''
        return self.get_ip_network()[node_id]

    def get_last_ip(self):
        return self.get_ip_network()[-2]

    def get_ip_network(self):
            return subnet_for_type()[type(self)]

    def get_mac(self, node_id):
        '''
        Get the mac address for the `node_id`.

        "02:01:00:00:01:00" -> Class: Mesh, Interface number 1, Node ID: 256 (0x100)

        Parameters
        ----------
        node_id : int

        Returns
        -------
        str
        '''
        nc = '%02x' % self.node_class
        nr_iface = '%02x' % self.nr_host_interface
        node_id = '%08x' % node_id

        return '%s:%s:%s:%s:%s:%s' % (nc, nr_iface, node_id[0:2], node_id[2:4], node_id[4:6], node_id[6:8])

    def get_network(self):
        ''' Get the network ip '''
        return self.get_ip_network()[-1]

    def get_netmask(self):
        ''' Get the net mask '''
        return self.get_ip_network().netmask

    # TODO: interface?
    def get_template_dict(self, node_id, *args, **kwargs):

        return {}

        # TODO: reactivate if get_ip() and all other methods used here are linked to NetworkConfigurator
        def f(s):
            return s % self.node_class_name

        return {
            f("ipv4_addr_%s_pred") : self.get_ip_pred(node_id),
            f("ipv4_addr_%s_suc") : self.get_ip_suc(node_id),
            f("ipv4_addr_%s") : self.get_ip(node_id),
            f("ipv4_network_%s") : self.get_network(),
            f("ipv4_netmask_%s") : self.get_netmask(),
        }

    #####################################################
    ### Automatically implemented through `get_ip`
    #####################################################

    def get_ip_pred(self, node_id):
        return self.get_ip(node_id - 1)

    def get_ip_suc(self, node_id):
        return self.get_ip(node_id + 1)

# TODO: DOC
class HubWiFi(Interface):

    node_class = 6
    node_class_name = "hubwifi"

    def __init__(self, *args, **kwargs):
        super(HubWiFi, self).__init__(*args, **kwargs)

class Management(Interface):

    node_class = 10
    node_class_name = "management"

    def __init__(self, *args, **kwargs):
        super(Management, self).__init__(*args, **kwargs)

class AP(Interface):

    node_class = 1
    node_class_name = "ap"

    def __init__(self, *args, **kwargs):
        super(AP, self).__init__(*args, **kwargs)

class Mesh(Interface):

    node_class = 2
    node_class_name = "mesh"

    def __init__(self, *args, **kwargs):
        super(Mesh, self).__init__(*args, **kwargs)

class ADHoc(Interface):

    node_class = 3
    node_class_name = "adhoc"

    def __init__(self, *args, **kwargs):
        super(ADHoc, self).__init__(*args, **kwargs)

class Bluetooth(Interface):

    node_class = 4
    node_class_name = "bluetooth"

    def __init__(self, *args, **kwargs):
        super(Bluetooth, self).__init__(*args, **kwargs)

class WifiDirect(Interface):

    node_class = 5
    node_class_name = "wifidirect"

    def __init__(self, *args, **kwargs):
        super(WifiDirect, self).__init__(*args, **kwargs)


def is_management_interface(interface):
    return type(interface) == Management

def is_hubwifi_interface(interface):
    return type(interface) == HubWiFi

# all interface types
INTERFACE_ALL_CLASSES_TYPES = {
    AP,
    Mesh,
    ADHoc,
    Bluetooth,
    WifiDirect,

    HubWiFi,
    Management
}


subnets = None
static_lock = Lock()

def subnet_for_type():
    '''

    Returns
    -------
    subnets : dict<type, IPv4Network>
        For each interface type a subnet.
    '''

    # there may be concurrent access
    with static_lock:
        global subnets
        if subnets is None:
            # TODO: make subnet configurable via scenario config!
            subnets = NetUtil.get_slash_x(ipaddress.ip_network(u"10.0.0.0/8").subnets(), 24)
            # for each interface type create an extra subnet
            subnets = dict(zip(INTERFACE_ALL_CLASSES_TYPES, subnets))
            subnets[Management] = ipaddress.ip_network(u"172.21.0.0/16")
        return subnets

# all interfaces which are treated equally
# the missing ones need sometimes special treatment
INTERFACE_NORMAL_CLASSES_TYPES = {
    HubWiFi,
    AP,
    Mesh,
    ADHoc,
    Bluetooth
}
INTERFACE_NAME_TYPE_MAPPING = {type.node_class_name: type for type in INTERFACE_ALL_CLASSES_TYPES}