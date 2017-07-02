from collections import defaultdict

from miniworld.errors import InterfaceUnknown
from miniworld.model.Objects import Objects
from miniworld.model.network.interface.Interface import INTERFACE_NORMAL_CLASSES_TYPES, INTERFACE_NAME_TYPE_MAPPING, AP, Mesh

__author__ = 'Nils Schmidt'

class Interfaces(Objects):
    '''
    Collection for the interfaces the OS has.
    Can be used like a list in python.

    Includes a factory method for the creation of multiple interfaces.
    '''


    def __init__(self, interfaces):
        '''
        Parameters
        ----------
        node_classes : list<Interface>
        '''
        self.interfaces = self.data = interfaces
        super(Interfaces, self).__init__(interfaces)

    @staticmethod
    def interface_name_to_type(interface_class_name):
        ''' Get the interface type for `interface_class_name`.

        Parameters
        ----------
        interface_class_name : str

        Returns
        -------
        type

        Raises
        ------
        InterfaceUnknown
        '''
        interface_class_name = interface_class_name.lower()
        type = INTERFACE_NAME_TYPE_MAPPING.get(interface_class_name)
        if type is None:
            raise InterfaceUnknown("The interface name '%s' is unknown!" % interface_class_name)
        return type

    @staticmethod
    def factory_from_interface_names(interface_names):
        ''' See py:meth:`.factory`

        Examples
        --------
        >>> Interfaces.factory_from_interface_names(["mesh"])
        [Mesh(1)]

        Raises
        ------
        InterfaceUnknown
        '''
        if not interface_names:
            return Interfaces([])
        else:
            return Interfaces.factory([Interfaces.interface_name_to_type(interface_name) for interface_name in interface_names])

    @staticmethod
    def factory(interface_types):
        '''
        Factory method to create the network interfaces.
        The factory takes care of counting interfaces of the same kind.
        This count+1 is passed to the `Interface` class (needed to differentiate between e.g. two `AP` objects)

        Parameters
        ----------
        interface_types: iterable<type>
            List of `Interface` types (uninitialized!)

        Returns
        -------
        Interfaces
        '''
        # count created instances
        counter = defaultdict(lambda : 1)
        interfaces = []

        for _type in interface_types:
            # create interface with current count
            interface = _type(counter[_type])
            interfaces.append( interface )
            # increment counter
            counter[_type] += 1

        return Interfaces(interfaces)

    # TODO: DOC
    def filter_mgmt(self):
        from miniworld.model.network.interface.Interface import Management
        return self.filter_type(Management)

    # TODO: DOC
    def filter_hub_wifi(self):
        from miniworld.model.network.interface.Interface import HubWiFi
        return self.filter_type(HubWiFi)

    def filter_normal_interfaces(self):
        return self.filter_type(fun = lambda _if : type(_if) in INTERFACE_NORMAL_CLASSES_TYPES)

    def iter_node_classes(self):
        return [nc.node_class for nc in self]

    def iter_node_classes_names(self):
        return [nc.node_class_name for nc in self]


if __name__ == '__main__':
    from miniworld.util import DictUtil
    interfaces = Interfaces.factory([Mesh, Mesh, AP, Mesh, AP])
    d = {}
    d[interfaces] = 1
    print(type(d.items()[0][0]))
    print(type(d.items()[0][1]))
    print(d)
    print(DictUtil.to_fully_staffed_matrix_2(d))
    #for i in Interfaces.factory([Mesh, Mesh, AP, Mesh, AP]):
    #    print i
