Concepts
========

.. contents:: Table of Contents
   :local:

.. note::

   This is a very short introduction into the basic concepts of MiniWorld. Please read the :doc:`master thesis <links>` for further documentation .

Network Backend
---------------

The network backend controls the virtual network. The Bridged WiFi network backend e.g. uses tools such as `iproute2 <https://wiki.linuxfoundation.org/networking/iproute2>`_ and `ebtables <http://ebtables.netfilter.org>`_ to create the network topology which is specified by *Movement Pattern*.
It takes care of creating new links, taking them up and down, creating switches etc.

Link Quality Model
------------------

The link quality between links is specified by a *Link Quality Model*.
Link quality models for the Bridged network backends rely on Linux network shaping (*tc* command). Queuing disciplines such as `HTB <http://lartc.org/manpages/tc-htb.html>`_ and `netem <https://wiki.linuxfoundation.org/networking/netem>`_ are used to control the link impairment between nodes.
Currently, only loss and delay is implemented.

Movement Pattern
----------------

The *Link Quality Model* takes the distance between nodes as input to create the link impairment.
The distance between nodes is determined by the *Movement Pattern*. At the time of writing, the `Core Mobility Pattern` may be the best choice.
It allows to define network topologies with the `CORE network emulation tool <https://www.nrl.navy.mil/itd/ncs/products/core>`_. Multiple of these core topologies can be created and then MiniWorld can switch between the topologies via a `mwcli step`.


Scenario Config
---------------

A **scenario config** holds all information about the number of VMs, how they shall be interconnected, which commands shall be run on the VM shells, defines the link quality model as well as the mobility pattern.

Let's have a look at the scenario config we used in the introduction (`examples/batman_adv.json`):

.. code-block:: json
   :linenos:

   {
     "scenario": "batman-adv",
     "cnt_nodes": 3,
     "walk_model": {
       "name": "core"
     },
     "provisioning": {
       "image": "examples/openwrt-15.05-x86-kvm_guest-combined-ext4_batman_adv.img",
       "regex_shell_prompt": "root@OpenWrt:/#",
       "shell": {
         "pre_network_start": {
           "shell_cmds": [
             "until ifconfig eth0; do echo -n . && sleep 1; done",
             "ifconfig eth0 0.0.0.0",
             "modprobe batman-adv",
             "batctl if add eth0",
             "iperf -s &"
           ]
         }
       }
     },
     "qemu": {
       "nic": {
         "model": "virtio-net-pci"
       }
        },
     "network": {
       "links": {
         "configuration": {
           "nic_prefix": "bat"
         },
         "model": "miniworld.model.network.linkqualitymodels.LinkQualityModelRange.LinkQualityModelWiFiExponential"
       },
       "core": {
         "topologies": [
           [
             0,
             "tests/core_topologies/chain5.xml"
           ],
           [
             0,
             "tests/core_topologies/wheel5.xml"
           ]
         ],
         "mode": "lan"
       }
     }
   }

**Root section**:

- 2: The scenario is named `batman-adv`
- 3: We want to start 3 VMs (nodes)

**Walk Model**

- 5: We use the **Core Mobility Pattern**

**Provisioning**

- 8: Declares the image to use for the VM. Note that for each node a custom image can be used
- 9: The shell prompt is used to determine when a VM has finished booting and for shell provisioning
- 12: The commands to be executed on each VM before the network is set up.

**Qemu**

- 24: Use the virtio NIC model for best bandwidth

**Network**

- 30: Provision IPs on all bat prefixed NICs inside the VM
- 32: Use the **LinkQualityModelWiFiExponential** to simulate the link impairment between nodes

