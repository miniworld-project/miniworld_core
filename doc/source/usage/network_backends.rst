Network Backends
================

A network backend is responsible to create and manage the network between VMs.
Currently there are 4 implemented network backends.
One of them may be removed in future releases and is not discussed in the following.

Basically there is one network backend for **wired** and one for **wireless** communication. 

Bridged LAN
-----------

Bridged WiFi (pseudo)
---------------------



The bridged network backends are based on Linux Bridges.

Bridged LAN uses for each connection between two nodes one tap device. Link shaping is done on the tap device since each tap device represents a connection. The number of connections have to be known beforehand, hence it is only usable with the Core Mobility Pattern. TODO: link

Two connected tap devices are put onto the same bridge.

The bridged WiFi network backend multiplexes connections via a single tap device. The different connections are marked in the Linux kernel such that for each connection a different link impairment can be set. All connections are put on the same hub (Linux bridge). For connected nodes ebtable rules allow communication. The broadcast behaviour of wireless networks is simulated with the hub mode. 
