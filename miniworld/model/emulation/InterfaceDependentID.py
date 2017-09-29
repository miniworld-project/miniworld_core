__author__ = 'Nils Schmidt'


class InterfaceDependentID:

    @staticmethod
    def get_interface_dependent_id(id, interface):
        return '%d_%d' % (id, interface)

    @staticmethod
    def get_interface_class_dependent_id(id, interface_class, interface_nr):
        return '%s_%d_%d' % (id, interface_class, interface_nr)
