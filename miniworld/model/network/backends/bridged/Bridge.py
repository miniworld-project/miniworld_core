from pprint import pformat
import netifaces

from miniworld.errors import NetworkBackendErrorReset
from miniworld.model.singletons.Singletons import singletons
from miniworld.model.network.backends import AbstractSwitch
from miniworld.model.network.backends.bridged.iproute2 import IPRoute2Commands

from miniworld.model.singletons import Resetable

__author__ = "Nils Schmidt"

# TODO: #54,#55: DOC


class Bridge(AbstractSwitch.AbstractSwitch, Resetable.Resetable):

    """
    Attributes
    ----------
    id : str
        Name of the bridge.
    bridge:

    See Also
    --------
    http://baturin.org/docs/iproute2/#Create%20a%20bridge%20interface
    http://lists.openwall.net/netdev/2015/06/16/44
    """

    def run(self, cmd):
        return singletons.shell_helper.run_shell(self.id, cmd, prefixes=["bridge"])

    def __init__(self, id, interface):
        super(Bridge, self).__init__(id, interface)
        # we want the shortened id due to the limitation of the tap device name length
        self.id = id

        self.bridge = None

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.id)

    ###############################################
    # Subclass stuff
    ###############################################

    # TODO: #54,#55: arguments needed for abstract start() ??
    # TODO: only allow starting once!
    def _start(self, bridge_dev_name=None, switch=False):
        """

        Parameters
        ----------
        bridge_dev_name : str, optional (default is None)
        switch : bool, optional (default is False)

        Returns
        -------

        Raises
        ------
        NetworkBackendStartError
        """
        self.bridge_dev_name = bridge_dev_name

    # TODO: #54,#55: exceptions around all networkbackends!
    # TODO: #54,#55: recognize or delete if_up
    def add_if(self, _if_name, if_up=True):
        """

        Parameters
        ----------
        _if_name

        Returns
        -------
        Raises
        ------
        NetworkBackendBridgedBridgeError
        """
        pass

    def reset(self):
        """
        Raises
        ------
        NetworkBackendErrorReset

        Returns
        -------

        """
        try:
            if self.started and self.bridge_dev_name:
                self.run(IPRoute2Commands.get_link_del_cmd(self.bridge_dev_name))

        except Exception as e:
            raise NetworkBackendErrorReset("""Could not shutdown the bridge '%s'
Interface dump:
%s
""" % (self, pformat(self.get_interfaces())), caused_by=e)

    @staticmethod
    def get_interfaces():
        # ip.by_name.keys()
        # return [x.get_attr('IFLA_IFNAME') for x in ipr.get_links()]
        return ', '.join(netifaces.interfaces())
