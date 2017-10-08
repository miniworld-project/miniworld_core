import threading
from collections import defaultdict

from miniworld.network.backends.bridged.iproute2.NetworkBackendBridged import NetworkBackendBridged
from miniworld.service.shell.ShellHelper import run_shell

lock = threading.Lock()

logger = None

"""
code from svinota for IPROUTE caching

from pyroute2 import IPRoute
ip = IPRoute()
ip.get_links()
[ (x.get_attr('IFLA_IFNAME'), x['index']) for x in ip.get_links() ]
dict([ (x.get_attr('IFLA_IFNAME'), x['index']) for x in ip.get_links() ])
ip.link("add", ifname="test", kind="dummy')
ip.link("add", ifname="test", kind="dummy")
dict([ (x.get_attr('IFLA_IFNAME'), x['index']) for x in ip.get_links() ])
cache = dict([ (x.get_attr('IFLA_IFNAME'), x['index']) for x in ip.get_links() ])
cache['test']
ip.link("set", index=cache['test'], state="up")
ip.get_links()
"""


def NetworkBackendBridgedPyroute2():
    class NetworkBackendBridgedPyroute2(NetworkBackendBridged.NetworkBackendBridged()):

        """
        Use pyroute2 to setup the network.
        """

        def __init__(self, network_backend_boot_strapper):
            super(NetworkBackendBridgedPyroute2, self).__init__(network_backend_boot_strapper)
            self.ipdb = None

        def get_ipdb(self):
            if self.ipdb is None:
                from pyroute2 import IPDB
                # https://github.com/svinota/pyroute2/issues/304#issuecomment-259275184
                import pyroute2.netlink.rtnl as rtnl
                GROUPS = \
                    rtnl.RTNLGRP_LINK | \
                    rtnl.RTNLGRP_NEIGH | \
                    rtnl.RTNLGRP_IPV4_IFADDR | \
                    rtnl.RTNLGRP_IPV4_ROUTE | \
                    rtnl.RTNLGRP_IPV4_MROUTE | \
                    rtnl.RTNLGRP_IPV6_IFADDR | \
                    rtnl.RTNLGRP_IPV6_ROUTE | \
                    rtnl.RTNLGRP_MPLS_ROUTE
                self.ipdb = IPDB(nl_async="process", nl_bind_groups=GROUPS)
                run_shell("chrt -f -p {} {}".format(1, self.ipdb.mnl.async_cache.pid))

            return self.ipdb

        def do_network_topology_change(self):
            with lock:
                super(NetworkBackendBridgedPyroute2, self).do_network_topology_change()
                try:
                    ipdb = self.get_ipdb()
                    self._logger.info("commit()")
                    ipdb.commit()
                except Exception as e:
                    try:
                        self._logger.critical(e.__dict__)
                    except BaseException:
                        pass

                    raise

        def reset(self):
            super(NetworkBackendBridgedPyroute2, self).reset()
            self._logger.debug("stopping ipdb instance")
            if self.ipdb:
                self.ipdb.release()
                self.ipdb = None

    return NetworkBackendBridgedPyroute2


def NetworkBackendBridgedPyroute2IPRoute():
    import pyroute2

    class NetworkBackendBridgedPyroute2IPRoute(NetworkBackendBridged.NetworkBackendBridged()):

        """
        Use pyroute2 to setup the network.
        """

        def __init__(self, network_backend_boot_strapper):
            super(NetworkBackendBridgedPyroute2IPRoute, self).__init__(network_backend_boot_strapper)

            self.ipr = pyroute2.IPRoute()
            self.last_step = -1
            self.step_cnt = 0
            self.ipb = pyroute2.IPBatch()
            self.cache = None
            self.created_bridges = set()
            self.reset_step_state()

        def reset_step_state(self):
            # TODO: REMOVE, replacable by p_links_add_bridge.keys()
            self.p_bridges = set()
            # bridge : link
            self.p_links_up = set()
            self.p_links_down = set()
            self.p_links_add_bridge = defaultdict(list)

        def before_simulation_step(self, simulation_manager, step_cnt, network_backend, emulation_nodes, **kwargs):
            self.step_cnt = step_cnt
            super(NetworkBackendBridgedPyroute2IPRoute, self).before_simulation_step(simulation_manager, step_cnt,
                                                                                     network_backend, emulation_nodes)
            self.reset_step_state()

        def build_cache(self):
            self._logger.info("building interface cache ...")
            self.cache = dict([(x.get_attr('IFLA_IFNAME'), x['index']) for x in self.ipr.get_links()])

        def get_iface_idx(self, iface):
            # return self.ipr.link_lookup(ifname=iface)[0]
            return self.cache[iface]

        def do_batch(self):
            self._logger.info("IPBatch sendto()")
            self.ipr.sendto(self.ipb.batch, (0, 0))

            self._logger.info("resetting batch object ...")
            self.ipb.reset()

        def do_network_topology_change(self):
            # TOOD: REMOVE?

            for bridge in set(self.p_links_add_bridge.keys()):
                if bridge not in self.created_bridges:
                    self.ipr.link("add", kind="bridge", ifname=bridge)
                    self.created_bridges.add(bridge)
            self.build_cache()
            # set hub mode
            for bridge in self.p_bridges:
                self.ipb.link("set", index=self.get_iface_idx(bridge), ageing_time=0)

            for bridge, links in self.p_links_add_bridge.items():
                for link in set(links):
                    self.ipb.link('set', index=self.get_iface_idx(link), master=self.get_iface_idx(bridge))
            # self.do_batch()

            for link in self.p_links_up:
                self.ipb.link('set', index=self.get_iface_idx(link), state='up')
            for link in self.p_links_add_bridge.keys():
                self.ipb.link('set', index=self.get_iface_idx(link), state='up')

            # self.do_batch()
            for link in self.p_links_down:
                self.ipb.link('set', index=self.get_iface_idx(link), state='down')
            self.do_batch()

            super(NetworkBackendBridgedPyroute2IPRoute, self).do_network_topology_change()

    return NetworkBackendBridgedPyroute2IPRoute
