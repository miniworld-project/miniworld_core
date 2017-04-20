Concepts
========


Scenario Config
---------------

Step
----

Network Backend
---------------

Link Quality Model
------------------

Movement Pattern
----------------

Scenario Config
---------------

A **scenario config** holds all information about the number of VMs, how they shall be interconnected, which commands shall be run on the VM shells, defines the link quality model as well as the mobility pattern.

Let's have a look at the scenario config we used in the introduction (`examples/batman_adv.json`):

.. literalinclude:: ../../../examples/batman_adv.json
   :language: json
   :linenos:

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

