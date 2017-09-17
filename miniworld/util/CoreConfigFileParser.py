import xml.dom.minidom
from collections import defaultdict, OrderedDict
from pprint import pprint

from miniworld.log import log

__author__ = "Nils Schmidt"


def parse_core_config_file(file_path, include_interfaces=False):
    '''
    Parse the core xml config file and return which nodes are connected with each other.

    Parameters
    ----------
    file_path : str
        Path to the core xml file

    Returns
    -------
    dict<int, set<int>
        Which nodes are connected to each other (upper triangular matrix)
    dict<(int, int), (int, int)>
        If include_interfaces

    The file looks like this:
    <?xml version="1.0" encoding="UTF-8"?>
    <scenario compiled="true" name="chain3.xml" version="1.0" xmlns="nmfPlan" xmlns:CORE="coreSpecific">
      <network id="net0" name="net0">
        <type>ethernet</type>
        <alias domain="COREID">36433</alias>
        <member type="interface">n1/eth0</member>
        <member type="interface">n2/eth0</member>
        <member type="channel">net0/chan0</member>
        <channel id="net0/chan0" name="chan0">
          <type>ethernet</type>
          <member index="0" type="interface">n1/eth0</member>
          <member index="1" type="interface">n2/eth0</member>
        </channel>
      </network>
      ...
      '''
    # Open XML document using minidom parser
    DOMTree = xml.dom.minidom.parse(file_path)
    scenario = DOMTree.documentElement
    version = scenario.getAttribute("version")
    log.debug("version: %s", version)
    check_version(version)

    # type:dict<int, list<int>>
    # store for each node the nodes which are connected to it
    connections = defaultdict(set) if not include_interfaces else {}

    networks = scenario.getElementsByTagName("network")
    for network in networks:
        log.debug("parsing network: %s", network.getAttribute("id"))

        for channel in network.getElementsByTagName("channel"):
            cur_node_id = None
            cur_interface = None
            for member in channel.getElementsByTagName("member"):
                if(member.getAttribute("type") == "interface"):
                    log.debug(member.childNodes[0].data)
                    # split "n1/eth1" to 1, 1
                    node_id, interface = member.childNodes[0].data.split("/")
                    node_id = int(node_id[1:])
                    interface = int(interface.split('eth')[1])
                    interface += 1

                    if cur_node_id is None:
                        cur_node_id = node_id
                        cur_interface = interface
                    else:
                        if include_interfaces:
                            connections[(cur_node_id, cur_interface)] = (node_id, interface)
                        else:
                            connections[cur_node_id].add(node_id)
                        if cur_node_id >= node_id:
                            if include_interfaces:
                                connections[(node_id, interface)] = (cur_node_id, cur_interface)
                            else:
                                connections[node_id].add(cur_node_id)
    return connections


def parse_core_config_file_positions(file_path):
    '''
    Parse the core xml config file and return the positions of the nodes.

    Parameters
    ----------
    file_path : str
        Path to the core xml file

    Returns
    -------
    dict<int, (float, float)>
        Node positions.

    The file looks like this:
    <?xml version="1.0" encoding="UTF-8"?>
    <scenario compiled="true" name="chain3.xml" version="1.0" xmlns="nmfPlan" xmlns:CORE="coreSpecific">
      <host id="n100" name="n100">
        <type domain="CORE">ServalNode</type>
        <interface id="n100/eth0" name="eth0">
          <member index="0" type="channel">net33/chan0</member>
          <member type="network">net33</member>
          <address type="mac">00:00:00:aa:00:be</address>
          <address type="IPv4">10.0.36.1/24</address>
          <address type="IPv6">2001:36::1/64</address>
        </interface>
        <alias domain="COREID">100</alias>
        <point lat="47.550510742" lon="-122.106359809" type="gps"/>
      </host>
    ...
    '''
    # Open XML document using minidom parser
    # TODO: #32: error handling!
    DOMTree = xml.dom.minidom.parse(file_path)
    scenario = DOMTree.documentElement
    version = scenario.getAttribute("version")
    log.debug("version: %s", version)
    check_version(version)

    # store for each node the position
    positions = OrderedDict()

    hosts = scenario.getElementsByTagName("host")
    for idx, host in enumerate(hosts, 1):
        # NOTE: we choose our own node ids because the ones in the core topology file may not start with 1
        host_id = idx
        log.debug("parsing host: %s", host_id)

        for point in host.getElementsByTagName("point"):
            lat = float(point.getAttribute("lat"))
            lon = float(point.getAttribute("lon"))

            positions[host_id] = (lat, lon)

    return positions


def check_version(version):
    if float(version) < 1.0:
        raise ValueError("Unsupported config file version! Should be 1.0 or greater!")


if __name__ == '__main__':

    # pprint(parse_core_config_file_positions('MiniWorld_Scenarios/serval_paper/core_scenarios/random_100_1.xml'))
    # pprint(parse_core_config_file("/Users/nils/Dropbox/uni/Master/my_nicer/playground/core-serval/docker/chain3.xml"))

    pprint(parse_core_config_file('MiniWorld_Scenarios/experiments/distributed/chain_512.xml'))
