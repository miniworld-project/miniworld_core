Network Backends
================

A network backend is responsible to create and manage the network between VMs.
Currently there are 3 implemented network backends.
One of them may be removed in future releases and is not discussed in the following.

Basically there is one network backend for **wired** and one for **wireless** communication. Both are based on Linux Bridges.

Bridged LAN uses for each connection between two nodes one tap device. Link shaping is done on the tap device since each tap device represents a connection.
