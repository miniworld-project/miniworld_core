Introduction
============

.. contents:: Table of Contents
   :local:

About
-----

MiniWorld is an acronym for `Mobile Infrastructure'n'Network Integrated World`.
Its purpose is to help evaluating/developing any kind of software that relies on network.
MiniWorld requires you to deploy the software-under-test in a VM.
A custom network topology can then be used to interconnect the VMs, additionally simulating link impairment such as delay, loss etc.

B.A.T.M.A.N Demo
----------------

In the following, a short demo on how to use MiniWorld is given.
For that purpose, we are going to start 3 OpenWRT nodes running the B.A.T.M.A.N. advanced routing algorithm.

Preparation
^^^^^^^^^^^

We are going to use 2 shells. In the first, we are going to start MiniWorld's server process.
In the second we are using a command-line tool to start the scenario.

In **shell 1** start the server process:

.. code-block:: bash

   $ mwserver

.. note::

   If for any reasons, MiniWorld won't stop correctly, you can force the server process to exit and perform the necessary cleanup with **./cleanup.sh**

In **shell 2**, start the scenario and wait until the command returns:

.. code-block:: bash

   mwcli start examples/batman_adv.json

In **shell 1** you should see the 3 OpenWRT VMs booting.

Ok, what have we done so far? We used a scenario file called `batman_adv.json` to boot 3 OpenWRT VMs with B.A.T.M.A.N. advanced.

The nodes are not yet interconnected. For that purpose we have to perform a **step**:

Connections/Links
^^^^^^^^^^^^^^^^^

Before we do that we check the connections and links. You can see that only connections to 'mgmt' exist.
This is due do the management where nodes are connected internally to a virtual node.

.. code-block:: bash

   $ mwcli info connections

   {
       "1": [
           "mgmt"
       ],
       "2": [
           "mgmt"
       ],
       "3": [
           "mgmt"
       ]
   }

.. code-block:: bash

   $ mwcli info links

   {
       "('1', 'mgmt')": null,
       "('2', 'mgmt')": null,
       "('3', 'mgmt')": null
   }

Create topology
^^^^^^^^^^^^^^^

Let's switch to the first topology and check the connections/links again.

.. code-block:: bash

   mwcli step


You can see that the first topology is a chain: 1 <-> 2 <-> 3.

.. code-block:: bash

   $ mwcli info connections

   {
       "1": [
           "2",
           "mgmt"
       ],
       "2": [
           "3",
           "mgmt"
       ],
       "3": [
           "mgmt"
       ]
   }

To both connections (1 <-> 2 and  2 <-> 3), a link impairment with 54000 bytes/s and a delay of 1s in each direction is applied.

.. code-block:: bash

   $ mwcli info links

   {
       "('1', '2')": {
           "delay": "1.00ms 0.10ms 25%",
           "reorder": null,
           "loss": null,
           "bandwidth": "54000.0",
           "duplicate": null,
           "limit": null,
           "corrupt": null,
           "rate": null
       },
       "('1', 'mgmt')": null,
       "('2', '3')": {
           "delay": "1.00ms 0.10ms 25%",
           "reorder": null,
           "loss": null,
           "bandwidth": "54000.0",
           "duplicate": null,
           "limit": null,
           "corrupt": null,
           "rate": null
       },
       "('2', 'mgmt')": null,
       "('3', 'mgmt')": null
   }


We can now check the neighbours of node 1:

.. code-block:: bash

   $ mwcli exec --node-id 1 'batctl o'

   [B.A.T.M.A.N. adv 2014.4.0, MainIF/MAC: eth0/02:01:00:00:00:01 (bat0 BATMAN_IV)]
     Originator      last-seen (#/255)           Nexthop [outgoingIF]:   Potential nexthops ...
   02:01:00:00:00:02    0.840s   (188) 02:01:00:00:00:02 [      eth0]: 02:01:00:00:00:02 (188)
   02:01:00:00:00:03    0.080s   (122) 02:01:00:00:00:02 [      eth0]: 02:01:00:00:00:02 (122)

Node 2 and node 3 are both reachable via node 2, hence the routing works since there is no direct connection between 1 <-> 3

.. code-block:: bash

   $ mwcli exec --node-id 1 'batctl tr 02:01:00:00:00:03'

   traceroute to 02:01:00:00:00:03 (02:01:00:00:00:03), 50 hops max, 20 byte packets
    1: 02:01:00:00:00:02  2.648 ms  2.586 ms  2.644 ms
    2: 02:01:00:00:00:03  5.840 ms  5.075 ms  5.412 ms

If we switch to the wheel topology where all nodes are connected with node 1, we can see that B.A.T.M.A.N. changed the routes accordingly.

.. code-block:: bash

   mwcli step

Node 3 is now reachable directly from node 1:

.. code-block:: bash

   $ mwcli exec --node-id 1 'batctl tr 02:01:00:00:00:03'

   traceroute to 02:01:00:00:00:03 (02:01:00:00:00:03), 50 hops max, 20 byte packets
    1: 02:01:00:00:00:03  2.687 ms  2.803 ms  3.050 ms


Stop the scenario
^^^^^^^^^^^^^^^^^

Before a new scenario can be started, the currently running scenario has to be stopped.
Further starts of the same scenario use the **snapshot boot mode** which uses KVM snapshots to enhance boot times drastically.

.. code-block:: bash

   mwcli stop

.. note::

   You may need to kill the server process when switching between different scenarios.