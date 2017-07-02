Network Backends
================

A network backend is responsible to create and manage the network between VMs.
Currently there are 3 implemented network backends.
One of them (VDE) may be removed in future releases and is not discussed in the following.

Basically there is one network backend for **wired** and one for **wireless** communication. 
The bridged network backends are based on Linux Bridges.

.. contents:: Table of Contents
   :local:

Bridged LAN
-----------

Bridged LAN uses for each connection between two nodes one tap device. Link shaping is done on the tap device since each tap device represents a connection. The number of connections have to be known beforehand, hence it is only usable with the Core Mobility Pattern. TODO: link
Two connected tap devices are put onto the same bridge.

Example
^^^^^^^

.. code-block:: bash

   mwcli start examples/nb_bridged_lan.json


Details
^^^^^^^

The following command shows how the nodes are connected to each other.There are 3 bridges: **mgmt** is the bridge for the management network. No link shaping is done on this network.
For each connection between two nodes are bridge is created. The bridges are prefixed with *br_*. *br_00001_00002* for example is the bridge for the connection between node 1 and node 2.

.. code-block:: bash

   $ brctl show
   bridge name	bridge id		STP enabled	interfaces
   br_00001_00002		8000.8a97fd2704ee	no		tap_00001_1
   							tap_00002_1
   br_00002_00003		8000.968ace0fbf60	no		tap_00002_2
   							tap_00003_1
   mgmt                 8000.329fcad5b6da	no		tap_00001_5
   							tap_00002_4
   							tap_00003_4

Bridged WiFi (pseudo)
---------------------

Example
^^^^^^^

The bridged WiFi network backend multiplexes connections via a single tap device. The different connections are marked in the Linux kernel such that for each connection a different link impairment can be set. All connections are put on the same hub (Linux bridge). For connected nodes ebtable rules allow communication.

.. code-block:: bash

   mwcli start examples/nb_bridged_wifi.json

Details
^^^^^^^

On **wifi1** links are shaped according to the link quality model.

.. code-block:: bash

   $ brctl show
   bridge name	bridge id		STP enabled	interfaces
   mgmt		8000.464c4db9ebb2	no		tap_00001_2
                               tap_00002_2
                               tap_00003_2
   wifi1	8000.5e9c09a15fb3	no		tap_00001_1
                               tap_00002_1
                               tap_00003_1

The connection firewall is done with ebtables:

.. code-block:: bash

   $ ebtables -L
   Bridge table: filter

   Bridge chain: INPUT, entries: 0, policy: ACCEPT

   Bridge chain: FORWARD, entries: 1, policy: ACCEPT
   --logical-in wifi1 -j wifi1

   Bridge chain: OUTPUT, entries: 0, policy: ACCEPT

   Bridge chain: wifi1, entries: 4, policy: DROP
   -i tap_00003_1 -o tap_00002_1 -j mark --mark-set 0x2 --mark-target ACCEPT
   -i tap_00002_1 -o tap_00003_1 -j mark --mark-set 0x2 --mark-target ACCEPT
   -i tap_00002_1 -o tap_00001_1 -j mark --mark-set 0x1 --mark-target ACCEPT
   -i tap_00001_1 -o tap_00002_1 -j mark --mark-set 0x1 --mark-target ACCEPT